"""Ollama integration for CrewAI - OpenAI-compatible API client.

Ollama provides OpenAI-compatible API at http://ollama:11434 which CrewAI can use
through a configured OpenAI client pointing to the Ollama endpoint. This enables
Apple Silicon GPU acceleration and local LLM inference.

This replaces the previous vLLM integration with Ollama for better macOS compatibility.
"""

from __future__ import annotations

from crewai import LLM
from typing import Optional


def get_llamacpp_llm(
    host: str = "http://ollama:11434",
    model_name: str = "qwen3:8b"
) -> LLM:
    """Factory function to create Ollama-powered LLM for CrewAI using OpenAI-compatible API.

    Since Ollama provides OpenAI-compatible endpoints, we configure CrewAI's LLM
    as an OpenAI provider pointing to the Ollama server for Apple Silicon GPU acceleration.

    Args:
        host: Ollama OpenAI-compatible API endpoint (Docker service: http://ollama:11434)
        model_name: Model identifier (must match what's loaded in Ollama)

    Returns:
        CrewAI LLM instance configured for Ollama
    """
    # Configure as OpenAI provider but point to Ollama's OpenAI-compatible endpoint
    # Ollama serves at /v1/chat/completions just like OpenAI API
    ollama_llm = LLM(
        model=f"openai/{model_name}",
        base_url=f"{host}/v1",
        api_key="not-needed-for-ollama"  # Ollama doesn't require API key for local serving
    )

    return ollama_llm
