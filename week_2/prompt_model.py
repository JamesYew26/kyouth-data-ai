"""Single entry point for talking to an LLM (Gemini in the cloud, or a local Ollama model).

Library functions raise LLMError instead of calling sys.exit(), so callers such as the
week_3 FastAPI backend can catch the failure and keep serving requests.

    uv run prompt_model.py gemini "Explain idempotency in one sentence"
"""

import argparse
import json
import os
import re
import sys
import time
from collections.abc import Callable
from typing import TypeVar

from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = os.getenv("LLM_MODEL", "gemini")
MODEL_ALIASES = {
    "gemini": "gemini-2.5-flash-lite",
    "deepseek": "deepseek-r1:1.5b",
}

T = TypeVar("T")


class LLMError(RuntimeError):
    """Raised when the model cannot be reached or returns an unusable response."""


def _query_gemini(model: str, prompt: str) -> str:
    from google import genai  # imported lazily so Ollama-only setups don't need it

    if not os.getenv("GEMINI_API_KEY"):
        raise LLMError("GEMINI_API_KEY is not set (add it to your .env file)")
    try:
        response = genai.Client().models.generate_content(model=model, contents=prompt)
    except Exception as exc:
        raise LLMError(f"Gemini request failed: {exc}") from exc
    if not response.text:
        raise LLMError("Gemini returned an empty response")
    return response.text


def _query_ollama(model: str, prompt: str) -> str:
    import ollama

    try:
        return ollama.generate(model=model, prompt=prompt)["response"]
    except ollama.ResponseError as exc:
        if exc.status_code == 404:
            raise LLMError(
                f"Ollama model '{model}' not found; run `ollama pull {model}`"
            ) from exc
        raise LLMError(f"Ollama error: {exc.error}") from exc
    except Exception as exc:
        raise LLMError(f"Could not reach Ollama (is it running?): {exc}") from exc


def prompt_model(model: str | None, prompt: str) -> str:
    """Send a prompt to Gemini (model names starting with 'gemini') or to Ollama."""
    model = MODEL_ALIASES.get(model or DEFAULT_MODEL, model or DEFAULT_MODEL)
    if model.lower().startswith("gemini"):
        return _query_gemini(model, prompt)
    return _query_ollama(model, prompt)


def parse_json_response(raw: str):
    """Parse JSON from an LLM reply, tolerating ```json fences and <think> blocks."""
    text = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise LLMError(f"Model did not return valid JSON: {text[:120]!r}") from exc


def with_retry(
    fn: Callable[[], T],
    retry_on: tuple[type[Exception], ...],
    max_attempts: int = 3,
    base_delay: float = 2.0,
    log: Callable[[str], None] = print,
) -> T:
    """Call fn(), retrying with exponential backoff (2s, 4s, ...) on the given errors."""
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except retry_on as exc:
            if attempt == max_attempts:
                raise
            delay = base_delay * 2 ** (attempt - 1)
            log(
                f"Attempt {attempt}/{max_attempts} failed: {exc}. Retrying in {delay:.0f}s"
            )
            time.sleep(delay)
    raise AssertionError("unreachable")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prompt Gemini or a local Ollama model."
    )
    parser.add_argument(
        "model", help="'gemini', 'deepseek', or any Gemini/Ollama model name"
    )
    parser.add_argument("prompt", help="prompt text")
    args = parser.parse_args()
    try:
        print(prompt_model(args.model, args.prompt))
    except LLMError as exc:
        sys.exit(f"Error: {exc}")


if __name__ == "__main__":
    main()
