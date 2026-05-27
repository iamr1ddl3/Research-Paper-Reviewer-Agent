import json
import re
import os

from openai import OpenAI

from app.config import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    OPENROUTER_REFERER,
    OPENROUTER_TITLE,
    DEFAULT_MAX_TOKENS,
)

_client: OpenAI | None = None


def client() -> OpenAI:
    global _client
    if _client is None:
        if not OPENROUTER_API_KEY:
            raise RuntimeError(
                "OPENROUTER_API_KEY missing. Populate .env from .env.example."
            )
        headers = {}
        if OPENROUTER_REFERER:
            headers["HTTP-Referer"] = OPENROUTER_REFERER
        if OPENROUTER_TITLE:
            headers["X-Title"] = OPENROUTER_TITLE
        _client = OpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
            default_headers=headers or None,
        )
    return _client


def call_llm(
    system_prompt: str,
    user_prompt: str,
    model: str,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> str:
    resp = client().chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    choice = resp.choices[0]
    if choice.finish_reason == "length":
        raise RuntimeError(
            f"LLM hit max_tokens={max_tokens} (finish_reason=length). Output likely truncated. "
            "Raise max_tokens or shorten input."
        )
    content = choice.message.content or ""
    if not content.strip():
        raise RuntimeError(f"LLM returned empty content. finish_reason={choice.finish_reason}")
    return content


_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def call_llm_json(
    system_prompt: str,
    user_prompt: str,
    model: str,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> dict:
    raw = call_llm(system_prompt, user_prompt, model, max_tokens)
    cleaned = raw.strip()
    fence = _FENCE_RE.search(cleaned)
    if fence:
        cleaned = fence.group(1).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(cleaned[start : end + 1])
        raise RuntimeError(f"LLM did not return valid JSON: {e}\nRaw:\n{raw[:1000]}")
