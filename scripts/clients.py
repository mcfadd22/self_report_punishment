"""Model clients for the pilot runner.

Every client takes a list of chat messages (role/content dicts) plus a system prompt and returns a dict:
  text      final response text
  thinking  reasoning text if the model returned any (Ollama thinking models, Claude summaries), else None
  stop      stop/finish reason as reported by the provider
  raw_model model name as reported by the provider

Providers:
  ollama     local models via Ollama's native /api/chat (stdlib only)
  openai     OpenAI-compatible /chat/completions: OpenAI, OpenRouter, vLLM (stdlib only)
  anthropic  Claude via the official anthropic SDK (pip install anthropic)
  mock       canned responses for testing the pipeline without any model
"""

import json
import os
import random
import re
import time
import urllib.error
import urllib.request

RETRYABLE_STATUS = {408, 409, 429, 500, 502, 503, 504}


class ClientError(Exception):
    pass


def _post_json(url, body, headers=None, timeout=600, retries=4):
    data = json.dumps(body).encode()
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, data=data, method="POST",
                                     headers={"Content-Type": "application/json", **(headers or {})})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")[:500]
            if e.code in RETRYABLE_STATUS and attempt < retries:
                time.sleep(min(2 ** attempt + random.random(), 60))
                continue
            raise ClientError(f"HTTP {e.code} from {url}: {detail}") from e
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt < retries:
                time.sleep(min(2 ** attempt + random.random(), 60))
                continue
            raise ClientError(f"could not reach {url}: {e}") from e


def _with_system(system, messages):
    return ([{"role": "system", "content": system}] if system else []) + messages


class OllamaClient:
    def __init__(self, cfg):
        self.cfg = cfg
        self.base = cfg.get("base_url", "http://localhost:11434")

    def check(self):
        try:
            with urllib.request.urlopen(f"{self.base}/api/tags", timeout=5) as resp:
                tags = json.loads(resp.read())
        except (urllib.error.URLError, TimeoutError) as e:
            raise ClientError(f"Ollama isn't running at {self.base} (start it with `ollama serve`)") from e
        names = {m["name"] for m in tags.get("models", [])}
        if self.cfg["model"] not in names and f"{self.cfg['model']}:latest" not in names:
            raise ClientError(f"model {self.cfg['model']} isn't pulled (run `ollama pull {self.cfg['model']}`)")

    def chat(self, system, messages, temperature, seed, max_tokens):
        options = {"num_predict": max_tokens, "seed": seed}
        if temperature is not None:
            options["temperature"] = temperature
        body = {"model": self.cfg["model"], "messages": _with_system(system, messages),
                "stream": False, "options": options}
        if "think" in self.cfg:
            body["think"] = self.cfg["think"]
        r = _post_json(f"{self.base}/api/chat", body)
        msg = r.get("message", {})
        return {"text": msg.get("content", ""), "thinking": msg.get("thinking") or None,
                "stop": r.get("done_reason"), "raw_model": r.get("model")}


class OpenAICompatibleClient:
    def __init__(self, cfg):
        self.cfg = cfg
        self.base = cfg.get("base_url", "https://api.openai.com/v1")
        self.key_env = cfg.get("api_key_env", "OPENAI_API_KEY")

    def check(self):
        if not os.environ.get(self.key_env):
            raise ClientError(f"set {self.key_env} to use {self.cfg['id']}")

    def chat(self, system, messages, temperature, seed, max_tokens):
        body = {"model": self.cfg["model"], "messages": _with_system(system, messages),
                "max_tokens": max_tokens, "seed": seed}
        if temperature is not None:
            body["temperature"] = temperature
        r = _post_json(f"{self.base}/chat/completions", body,
                       headers={"Authorization": f"Bearer {os.environ[self.key_env]}"})
        choice = r["choices"][0]
        msg = choice.get("message", {})
        return {"text": msg.get("content") or "", "thinking": msg.get("reasoning") or None,
                "stop": choice.get("finish_reason"), "raw_model": r.get("model")}


class AnthropicClient:
    """Claude via the SDK. Current Claude models reject custom temperature and can't turn thinking off,
    so sampling runs at the model default; effort and thinking display come from the model config."""

    def __init__(self, cfg):
        self.cfg = cfg
        self.client = None

    def check(self):
        try:
            import anthropic
        except ImportError as e:
            raise ClientError("pip install anthropic to use Claude models") from e
        self.client = anthropic.Anthropic(max_retries=4)

    def chat(self, system, messages, temperature, seed, max_tokens):
        kwargs = {"model": self.cfg["model"], "max_tokens": self.cfg.get("max_tokens", max_tokens),
                  "messages": messages,
                  "thinking": {"type": "adaptive", "display": "summarized"},
                  "output_config": {"effort": self.cfg.get("effort", "medium")}}
        if system:
            kwargs["system"] = system
        r = self.client.messages.create(**kwargs)
        text = "".join(b.text for b in r.content if b.type == "text")
        thinking = "\n".join(b.thinking for b in r.content if b.type == "thinking" and b.thinking) or None
        return {"text": text, "thinking": thinking, "stop": r.stop_reason, "raw_model": r.model}


class MockClient:
    """Returns well-formed answers of the right shape so the full pipeline can be tested offline."""

    def __init__(self, cfg):
        self.cfg = cfg

    def check(self):
        pass

    def chat(self, system, messages, temperature, seed, max_tokens):
        rng = random.Random(seed)
        prompt = messages[-1]["content"]
        if '"detection_fraction"' in prompt:
            text = json.dumps({"detection_fraction": "1 in 2", "mental_state": "recognized the risk and went ahead",
                               "reoffense_likelihood": rng.randint(1, 7)})
        elif '"counterfactual_sentence"' in prompt:
            text = json.dumps({"sentence": rng.randint(0, 120), "counterfactual_sentence": rng.randint(0, 120)})
        elif '"percent_change"' in prompt:
            text = json.dumps({"direction": rng.choice(["longer", "shorter", "same"]), "percent_change": rng.randint(0, 50)})
        elif '"choice"' in prompt:
            text = json.dumps({"choice": rng.choice("ABCDE")})
        elif "100 points" in prompt or "Distribute 100" in prompt:
            text = json.dumps(dict(zip("ABCDE", [20] * 5)))
        elif re.search(r"\b1 \(|from 0 \(", prompt):
            text = json.dumps({k: rng.randint(1, 7) for k in "ABCDE"})
        elif '{"sentence": <months>}.' in prompt:
            text = json.dumps({"sentence": rng.randint(0, 120)})
        elif "first line" in prompt:
            text = f"{rng.randint(0, 120)}\nThe defendant's mental state determined the sentence."
        else:
            text = "Punishment should track what the offender deserves."
        return {"text": text, "thinking": None, "stop": "stop", "raw_model": "mock"}


PROVIDERS = {"ollama": OllamaClient, "openai": OpenAICompatibleClient,
             "anthropic": AnthropicClient, "mock": MockClient}


def make_client(cfg):
    return PROVIDERS[cfg["provider"]](cfg)
