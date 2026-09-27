"""
Thin client for calling an LLM through OpenRouter.

Model choice: openai/gpt-4o-mini (default, overridable via OPENROUTER_MODEL).
Why this model:
  - Fast and inexpensive on OpenRouter, well suited to a live hackathon demo
    where latency and cost both matter.
  - Strong, reliable instruction-following for two lightweight jobs here:
    (1) turning a business question into a constrained SQL SELECT, and
    (2) summarizing a small set of retrieved rows into a grounded answer.
  - Both of those tasks are short-context and don't need a large/expensive
    frontier model; a small, cheap model is sufficient and keeps the demo
    fast and reliable.
  - Any OpenRouter chat model can be swapped in via the OPENROUTER_MODEL
    env var (e.g. "anthropic/claude-3.5-haiku", "google/gemini-2.0-flash-001",
    "meta-llama/llama-3.1-8b-instruct") without code changes.
"""

import requests

from .config import Config


class LLMError(Exception):
    pass


def chat(system_prompt: str, user_prompt: str, temperature: float = 0.0) -> str:
    """Call OpenRouter's chat completions endpoint and return the text reply."""
    if not Config.OPENROUTER_API_KEY:
        raise LLMError("OPENROUTER_API_KEY is not set. Check your .env file.")

    headers = {
        "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        # Optional but recommended by OpenRouter for analytics/rate-limit context
        "HTTP-Referer": "https://github.com/",
        "X-Title": "Banking Gold RAG Assistant",
    }

    payload = {
        "model": Config.OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
    }

    try:
        resp = requests.post(
            Config.OPENROUTER_BASE_URL,
            headers=headers,
            json=payload,
            timeout=Config.QUERY_TIMEOUT_SECONDS,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise LLMError(f"OpenRouter request failed: {exc}") from exc

    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError) as exc:
        raise LLMError(f"Unexpected OpenRouter response: {data}") from exc
