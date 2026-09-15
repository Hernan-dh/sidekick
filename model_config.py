"""Provider-aware LangChain models for Sidekick."""

from __future__ import annotations

import os
from dataclasses import dataclass

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_openrouter import ChatOpenRouter


@dataclass(frozen=True)
class ModelSet:
    """Available models in configured provider priority order."""

    primary: BaseChatModel
    fallbacks: tuple[BaseChatModel, ...]
    providers: tuple[str, ...]
    labels: tuple[str, ...]


def _configured(name: str) -> bool:
    return bool(os.getenv(name, "").strip())


def configured_models(list_name: str, legacy_name: str, defaults: tuple[str, ...]) -> tuple[str, ...]:
    """Read a comma-separated model chain, keeping legacy singular settings useful."""
    configured = os.getenv(list_name, "").strip()
    if configured:
        models = tuple(item.strip() for item in configured.split(",") if item.strip())
    elif legacy := os.getenv(legacy_name, "").strip():
        models = (legacy, *defaults)
    else:
        models = defaults
    return tuple(dict.fromkeys(models))


def build_models(*, temperature: float = 0) -> ModelSet:
    """Build Gemini, Groq, and OpenRouter models from configured credentials.

    Provider order can be changed with SIDEKICK_PROVIDER_ORDER. Providers without
    credentials are skipped, and startup fails clearly if none are configured.
    """

    available: dict[str, list[tuple[str, BaseChatModel]]] = {}
    if _configured("GEMINI_API_KEY"):
        available["gemini"] = [
            (
                name,
                ChatGoogleGenerativeAI(
                    model=name, google_api_key=os.environ["GEMINI_API_KEY"], max_retries=1
                ),
            )
            for name in configured_models(
                "SIDEKICK_GEMINI_MODELS",
                "GEMINI_MODEL",
                ("gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.6-flash"),
            )
        ]
    if _configured("GROQ_API_KEY"):
        available["groq"] = [
            (
                name,
                ChatGroq(model=name, api_key=os.environ["GROQ_API_KEY"], temperature=temperature, max_retries=1),
            )
            for name in configured_models(
                "SIDEKICK_GROQ_MODELS",
                "GROQ_MODEL",
                ("openai/gpt-oss-120b", "qwen/qwen3.8-27b"),
            )
        ]
    if _configured("OPENROUTER_API_KEY"):
        available["openrouter"] = [
            (
                name,
                ChatOpenRouter(
                    model=name,
                    api_key=os.environ["OPENROUTER_API_KEY"],
                    temperature=temperature,
                    max_retries=1,
                    app_url=None,
                    app_title=None,
                ),
            )
            for name in configured_models(
                "SIDEKICK_OPENROUTER_MODELS",
                "OPENROUTER_MODEL",
                (
                    "nvidia/nemotron-3-ultra-550b-a55b:free",
                    "nvidia/nemotron-3-super-120b-a12b:free",
                    "cohere/north-mini-code:free",
                ),
            )
        ]

    requested = [
        item.strip().lower()
        for item in os.getenv("SIDEKICK_PROVIDER_ORDER", "gemini,groq,openrouter").split(",")
        if item.strip()
    ]
    unknown = sorted(set(requested) - {"gemini", "groq", "openrouter"})
    if unknown:
        raise RuntimeError(f"Unknown providers in SIDEKICK_PROVIDER_ORDER: {', '.join(unknown)}")
    selected = [(provider, model_name, model) for provider in requested for model_name, model in available.get(provider, [])]
    if not selected:
        raise RuntimeError(
            "No model provider is configured. Set GEMINI_API_KEY, GROQ_API_KEY, "
            "or OPENROUTER_API_KEY in .env."
        )
    providers = tuple(provider for provider, _, _ in selected)
    labels = tuple(f"{provider}/{model_name}" for provider, model_name, _ in selected)
    models = tuple(model for _, _, model in selected)
    return ModelSet(primary=models[0], fallbacks=models[1:], providers=providers, labels=labels)


def build_structured_evaluator(schema: type):
    """Build a provider-fallback runnable that returns the evaluator schema."""

    models = build_models(temperature=0)
    structured = [model.with_structured_output(schema) for model in (models.primary, *models.fallbacks)]
    return structured[0].with_fallbacks(structured[1:]) if len(structured) > 1 else structured[0]
