"""Model adapter. One class per backend; all return TurnResult."""

import json
import time
from dataclasses import dataclass, field

from openai import OpenAI


@dataclass
class TurnResult:
    text: str | None
    tool_calls: list = field(default_factory=list)  # [{id, name, args}]
    latency_ms: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    finish_reason: str = ""
    served_model: str = ""  # what LM Studio reports actually served the request
    error: str | None = None


class LMStudioAdapter:
    """Talks to LM Studio's OpenAI-compatible server."""

    def __init__(self, base_url="http://localhost:1234/v1", api_key="lm-studio"):
        self.client = OpenAI(base_url=base_url, api_key=api_key)

    def chat(self, model, messages, tools=None, max_tokens=1024, temperature=0.0):
        kwargs = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        start = time.perf_counter()
        try:
            resp = self.client.chat.completions.create(**kwargs)
        except Exception as e:
            return TurnResult(
                text=None,
                latency_ms=(time.perf_counter() - start) * 1000,
                finish_reason="error",
                error=f"{type(e).__name__}: {e}",
            )

        latency_ms = (time.perf_counter() - start) * 1000
        choice = resp.choices[0]
        msg = choice.message

        tool_calls = []
        for tc in msg.tool_calls or []:
            try:
                args = json.loads(tc.function.arguments)
                parse_error = False
            except Exception:
                args = {"_raw": tc.function.arguments}
                parse_error = True
            tool_calls.append({
                "id": tc.id,
                "name": tc.function.name,
                "args": args,
                "parse_error": parse_error,
            })

        usage = resp.usage
        return TurnResult(
            text=msg.content,
            tool_calls=tool_calls,
            latency_ms=latency_ms,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            finish_reason=choice.finish_reason or "",
            served_model=getattr(resp, "model", "") or "",
        )

    def list_models(self):
        """Return list of model IDs LM Studio currently exposes."""
        try:
            return [m.id for m in self.client.models.list().data]
        except Exception as e:
            return {"error": f"{type(e).__name__}: {e}"}

    def warmup(self, model):
        """Force-load a model with a tiny no-op call. Returns latency_ms or error."""
        return self.chat(model, [{"role": "user", "content": "hi"}], tools=None, max_tokens=1)
