from __future__ import annotations

"""Lightweight LLM client implementations.

This module defines a ``BaseLLMClient`` along with concrete clients for
Gemini and HuggingFace models.  The clients here are intentionally
minimal and serve primarily as extension points; they provide a common
interface used by ``PersonaLLM`` for dispatching calls based on provider
and model identifiers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Tuple


class BaseLLMClient(ABC):
    """Abstract base class for simple text generation clients."""

    def __init__(self, model: str) -> None:
        self.model = model

    @abstractmethod
    def generate(self, prompt: str, **kwargs: Dict) -> str:
        """Generate text for ``prompt``.

        Concrete implementations may choose to ignore ``kwargs``.  The
        method is synchronous to keep tests simple.
        """


class GeminiClient(BaseLLMClient):
    """Placeholder client for Google's Gemini models."""

    provider = "google"

    def generate(self, prompt: str, **kwargs: Dict) -> str:  # pragma: no cover - trivial
        return f"Gemini({self.model}) response to: {prompt}"[:100]


class HuggingFaceClient(BaseLLMClient):
    """Placeholder client for HuggingFace models."""

    provider = "huggingface"

    def generate(self, prompt: str, **kwargs: Dict) -> str:  # pragma: no cover - trivial
        return f"HF({self.model}) response to: {prompt}"[:100]


_CLIENT_FACTORIES: Dict[str, type[BaseLLMClient]] = {
    GeminiClient.provider: GeminiClient,
    HuggingFaceClient.provider: HuggingFaceClient,
}


def create_llm_client(provider: str, model: str) -> BaseLLMClient:
    """Factory creating a client for ``provider`` and ``model``.

    Args:
        provider: LLM provider identifier, e.g. ``"google"``.
        model:    Model name associated with the provider.
    """
    try:
        factory = _CLIENT_FACTORIES[provider]
    except KeyError:  # pragma: no cover - defensive
        raise ValueError(f"Unsupported provider: {provider}")
    return factory(model)
