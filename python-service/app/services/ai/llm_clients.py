from __future__ import annotations

"""Lightweight LLM client implementations.

This module defines a ``BaseLLMClient`` along with concrete clients for
Ollama, OpenAI, and Gemini models. The clients provide a common interface 
used by ``PersonaLLM`` for dispatching calls based on provider and model 
identifiers with automatic fallback support.
"""

from abc import ABC, abstractmethod
from typing import Dict, Tuple, Optional
import asyncio
import httpx
from loguru import logger

try:
    import ollama
except ImportError:
    ollama = None

try:
    import openai
except ImportError:
    openai = None

try:
    from google import genai
except ImportError:
    genai = None

from ...core.config import resolve_api_key


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

    def is_available(self) -> bool:
        """Check if this client is available and properly configured."""
        return True


class OllamaClient(BaseLLMClient):
    """Client for Ollama local models."""

    provider = "ollama"

    def __init__(self, model: str, host: str = "http://localhost:11434") -> None:
        super().__init__(model)
        self.host = host

    def is_available(self) -> bool:
        """Check if Ollama service is available."""
        if ollama is None:
            logger.warning("Ollama client not available - package not installed")
            return False

        try:
            # Quick health check
            response = httpx.get(f"{self.host}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama service not available at {self.host}: {e}")
            return False

    def generate(self, prompt: str, **kwargs: Dict) -> str:
        """Generate text using Ollama."""
        if not self.is_available():
            raise ConnectionError(f"Ollama service not available at {self.host}")

        try:
            # Use ollama client
            client = ollama.Client(host=self.host)
            response = client.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                options=kwargs.get("options", {})
            )
            return response["message"]["content"]
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise


class OpenAIClient(BaseLLMClient):
    """Client for OpenAI models."""

    provider = "openai"

    def __init__(self, model: str) -> None:
        super().__init__(model)
        self.api_key = resolve_api_key("openai")
        if openai and self.api_key:
            self.client = openai.OpenAI(api_key=self.api_key)
        else:
            self.client = None

    def is_available(self) -> bool:
        """Check if OpenAI client is available."""
        if openai is None:
            logger.warning("OpenAI client not available - package not installed")
            return False
        if not self.api_key:
            logger.warning("OpenAI API key not configured")
            return False
        return True

    def generate(self, prompt: str, **kwargs: Dict) -> str:
        """Generate text using OpenAI."""
        if not self.is_available():
            raise ValueError("OpenAI client not properly configured")
            
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=kwargs.get("max_tokens", 1000),
                temperature=kwargs.get("temperature", 0.7)
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise


class GeminiClient(BaseLLMClient):
    """Client for Google's Gemini models."""

    provider = "gemini"

    def __init__(self, model: str) -> None:
        super().__init__(model)
        self.api_key = resolve_api_key("gemini")
        if genai and self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    def is_available(self) -> bool:
        """Check if Gemini client is available."""
        if genai is None:
            logger.warning("Gemini client not available - package not installed")
            return False
        if not self.api_key:
            logger.warning("Gemini API key not configured")
            return False
        return True

    def generate(self, prompt: str, **kwargs: Dict) -> str:
        """Generate text using Gemini."""
        if not self.is_available():
            raise ValueError("Gemini client not properly configured")
            
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            raise


_CLIENT_FACTORIES: Dict[str, type[BaseLLMClient]] = {
    OllamaClient.provider: OllamaClient,
    OpenAIClient.provider: OpenAIClient,
    GeminiClient.provider: GeminiClient,
}


def create_llm_client(provider: str, model: str, **kwargs) -> BaseLLMClient:
    """Factory creating a client for ``provider`` and ``model``.

    Args:
        provider: LLM provider identifier, e.g. ``"ollama"``, ``"openai"``, ``"gemini"``.
        model:    Model name associated with the provider.
        **kwargs: Additional arguments passed to client constructor.
    """
    try:
        factory = _CLIENT_FACTORIES[provider]
    except KeyError:  # pragma: no cover - defensive
        raise ValueError(f"Unsupported provider: {provider}")
    return factory(model, **kwargs)


class LLMRouter:
    """Routes LLM requests with automatic fallback between providers."""

    def __init__(self, preferences: str = "ollama:gemma3:1b,openai:gpt-4o-mini,gemini:gemini-1.5-flash"):
        """Initialize router with provider preferences.

        Args:
            preferences: Comma-separated list of provider:model pairs in preference order.
                        e.g. "ollama:gemma3:1b,openai:gpt-4o-mini,gemini:gemini-1.5-flash"
        """
        self.providers = self._parse_preferences(preferences)
        self._clients = {}
        logger.info(f"LLM Router initialized with providers: {[p[0] for p in self.providers]}")

    def _parse_preferences(self, preferences: str) -> list[Tuple[str, str]]:
        """Parse preference string into list of (provider, model) tuples."""
        providers = []
        for pref in preferences.split(','):
            pref = pref.strip()
            if ':' in pref:
                provider, model = pref.split(':', 1)
                providers.append((provider.strip(), model.strip()))
            else:
                logger.warning(f"Invalid preference format: {pref}, expected 'provider:model'")
        return providers

    def _get_client(self, provider: str, model: str) -> BaseLLMClient:
        """Get or create client for provider/model pair."""
        key = (provider, model)
        if key not in self._clients:
            kwargs = {}
            if provider == "ollama":
                # Allow configurable Ollama host
                from ...core.config import get_settings
                settings = get_settings()
                ollama_host = getattr(settings, 'ollama_host', 'http://localhost:11434')
                kwargs['host'] = ollama_host

            self._clients[key] = create_llm_client(provider, model, **kwargs)
        return self._clients[key]

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text with fallback through provider list."""
        last_error = None

        for provider, model in self.providers:
            try:
                client = self._get_client(provider, model)
                if client.is_available():
                    logger.debug(f"Using LLM provider: {provider}:{model}")
                    return client.generate(prompt, **kwargs)
                else:
                    msg = f"Provider {provider}:{model} not available"
                    logger.warning(f"{msg}, trying next")
                    if last_error is None:
                        last_error = RuntimeError(msg)
                    continue
            except Exception as e:
                logger.warning(f"Provider {provider}:{model} failed: {e}, trying next")
                last_error = e
                continue

        # All providers failed
        if last_error is None:
            error_msg = "All LLM providers failed. No providers were available"
        else:
            error_msg = f"All LLM providers failed. Last error: {last_error}"
        logger.error(error_msg)
        raise ConnectionError(error_msg)

    def get_available_providers(self) -> list[Tuple[str, str, bool]]:
        """Get list of configured providers and their availability status."""
        results = []
        for provider, model in self.providers:
            try:
                client = self._get_client(provider, model)
                available = client.is_available()
            except Exception:
                available = False
            results.append((provider, model, available))
        return results