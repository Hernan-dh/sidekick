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


def _configured(name: str) -> bool:
    return bool(os.getenv(name, "").strip())


def build_models(*, temperature: float = 0) -> ModelSet:
    """Build Gemini, Groq, and OpenRouter models from configured credentials.

    Provider order can be changed with SIDEKICK_PROVIDER_ORDER. Providers without
    credentials are skipped, and startup fails clearly if none are configured.
    """

    available: dict[str, BaseChatModel] = {}
    if _configured("GEMINI_API_KEY"):
        available["gemini"] = ChatGoogleGenerativeAI(
            model=os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
            google_api_key=os.environ["GEMINI_API_KEY"],
            temperature=temperature,
            max_retries=1,
        )
    if _configured("GROQ_API_KEY"):
        available["groq"] = ChatGroq(
            model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
            api_key=os.environ["GROQ_API_KEY"],
            temperature=temperature,
            max_retries=1,
        )
    if _configured("OPENROUTER_API_KEY"):
        available["openrouter"] = ChatOpenRouter(
            model=os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-120b"),
            api_key=os.environ["OPENROUTER_API_KEY"],
            temperature=temperature,
            max_retries=1,
            app_url=None,
            app_title=None,
        )

    requested = [
        item.strip().lower()
        for item in os.getenv("SIDEKICK_PROVIDER_ORDER", "gemini,groq,openrouter").split(",")
        if item.strip()
    ]
    unknown = sorted(set(requested) - {"gemini", "groq", "openrouter"})
    if unknown:
        raise RuntimeError(f"Unknown providers in SIDEKICK_PROVIDER_ORDER: {', '.join(unknown)}")
    providers = tuple(name for name in requested if name in available)
    if not providers:
        raise RuntimeError(
            "No model provider is configured. Set GEMINI_API_KEY, GROQ_API_KEY, "
            "or OPENROUTER_API_KEY in .env."
        )
    models = tuple(available[name] for name in providers)
    return ModelSet(primary=models[0], fallbacks=models[1:], providers=providers)


def build_structured_evaluator(schema: type):
    """Build a provider-fallback runnable that returns the evaluator schema."""

    models = build_models(temperature=0)
    structured = [model.with_structured_output(schema) for model in (models.primary, *models.fallbacks)]
    return structured[0].with_fallbacks(structured[1:]) if len(structured) > 1 else structured[0]
