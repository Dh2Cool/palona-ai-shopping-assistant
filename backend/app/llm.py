"""LLM adapter: Ollama (local) with fallback to Groq (deployed)."""

import base64
import os
from typing import Any

# Try Ollama first (local)
try:
    import httpx
except ImportError:
    httpx = None  # type: ignore


OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
GROQ_API_KEY = (os.getenv("GROQ_API_KEY") or "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_VISION_MODEL = os.getenv(
    "GROQ_VISION_MODEL",
    "meta-llama/llama-4-scout-17b-16e-instruct",  # Llama 4 Scout vision
)
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_VISION_MODEL = os.getenv("OLLAMA_VISION_MODEL", "llava")


def _use_groq() -> bool:
    """Use Groq when API key is set (deployed mode)."""
    return bool(GROQ_API_KEY)


async def chat_completion(
    messages: list[dict[str, Any]],
    temperature: float = 0.7,
) -> str:
    """Send chat completion request to Ollama or Groq."""
    if _use_groq():
        return await _groq_chat(messages, temperature)
    return await _ollama_chat(messages, temperature)


async def _ollama_chat(messages: list[dict[str, Any]], temperature: float) -> str:
    """Ollama chat API."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(
            f"{OLLAMA_BASE}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": messages,
                "stream": False,
                "options": {"temperature": temperature},
            },
        )
        r.raise_for_status()
        data = r.json()
        return data.get("message", {}).get("content", "").strip()


async def _groq_chat(messages: list[dict[str, Any]], temperature: float) -> str:
    """Groq chat API."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "messages": messages,
                "temperature": temperature,
            },
        )
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"].strip()


async def describe_image(image_base64: str) -> str:
    """
    Use vision model to describe an image.
    Ollama: LLaVA. Groq: llama-3.2-90b-vision-preview or similar.
    """
    if _use_groq():
        return await _groq_vision(image_base64)
    return await _ollama_vision(image_base64)


def _extract_base64(image_data: str) -> str:
    """Extract raw base64 string from data URL or return as-is if already raw."""
    if image_data.startswith("data:"):
        # Format: data:image/png;base64,iVBORw0KGgo...
        parts = image_data.split(",", 1)
        return parts[1] if len(parts) == 2 else image_data
    return image_data


async def _ollama_vision(image_base64: str) -> str:
    """Ollama LLaVA for image description. Expects raw base64 (no data URL prefix)."""
    raw_base64 = _extract_base64(image_base64)

    async with httpx.AsyncClient(timeout=90.0) as client:
        r = await client.post(
            f"{OLLAMA_BASE}/api/chat",
            json={
                "model": OLLAMA_VISION_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            "Describe this image in detail for product search. "
                            "Focus on: clothing style, colors, type of product, "
                            "materials, occasion, and any visible features. "
                            "Output a short product search query (1-2 sentences)."
                        ),
                        "images": [raw_base64],
                    }
                ],
                "stream": False,
            },
        )
        r.raise_for_status()
        data = r.json()
        return data.get("message", {}).get("content", "").strip()


async def _groq_vision(image_base64: str) -> str:
    """Groq vision API using Llama 4 Scout or Maverick."""
    if not image_base64.startswith("data:"):
        image_base64 = f"data:image/jpeg;base64,{image_base64}"

    async with httpx.AsyncClient(timeout=90.0) as client:
        r = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_VISION_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "Describe this image for product search. "
                                    "Focus on: clothing style, colors, product type, "
                                    "materials, occasion. Output 1-2 sentences as a product search query."
                                ),
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": image_base64},
                            },
                        ],
                    }
                ],
                "max_tokens": 150,
            },
        )
        if r.status_code != 200:
            # Vision may not be available; return generic fallback
            return "casual clothing or accessories"
        data = r.json()
        return data["choices"][0]["message"]["content"].strip()


def is_ollama_available() -> bool:
    """Check if Ollama is reachable (sync, for startup)."""
    if _use_groq():
        return True
    try:
        r = httpx.get(f"{OLLAMA_BASE}/api/tags", timeout=5.0)
        return r.status_code == 200
    except Exception:
        return False
