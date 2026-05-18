from __future__ import annotations

import json
import logging

import httpx

from dbms_vendor_analyzer.config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT

logger = logging.getLogger(__name__)


class OllamaError(Exception):
    pass


async def call_llm(prompt: str, *, model: str = OLLAMA_MODEL) -> str:
    """Send a prompt to Ollama and return the response text."""
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.0},
        "think": False,
    }
    async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
        try:
            resp = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise OllamaError(f"Ollama request failed: {exc}") from exc

    data = resp.json()
    return data.get("response", "").strip()


async def call_llm_json(prompt: str, *, model: str = OLLAMA_MODEL) -> dict:  # type: ignore[type-arg]
    """Call Ollama and parse the response as JSON. Raises OllamaError on failure."""
    raw = await call_llm(prompt, model=model)

    # Strip markdown code fences if the model wraps output
    cleaned = raw
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        cleaned = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise OllamaError(f"LLM returned non-JSON: {exc}\nRaw: {raw[:500]}") from exc
