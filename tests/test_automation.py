"""Regression tests for the dependency-free repository automation."""

from __future__ import annotations

import importlib.util
import os
import sys
import unittest
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


publish = load_module("publish", ROOT / "scripts" / "publish.py")
model_config = None


class RequestStub:
    messages = []

    def override(self, **changes):
        return changes["model"]


class PublishMetadataTests(unittest.TestCase):
    def test_accepts_conventional_metadata(self) -> None:
        self.assertEqual(
            publish.validate("docs: explain publishing", "Document the safe publication workflow."),
            ("docs: explain publishing", "Document the safe publication workflow."),
        )


class ModelConfigurationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        global model_config
        model_config = load_module("model_config", ROOT / "model_config.py")

    def test_requires_at_least_one_provider(self) -> None:
        assert model_config is not None
        keys = {
            "GEMINI_API_KEY": "", "GROQ_API_KEY": "", "OPENROUTER_API_KEY": "",
            "SIDEKICK_PROVIDER_ORDER": "gemini,groq,openrouter", "SIDEKICK_GEMINI_MODELS": "",
        }
        with patch.dict(os.environ, keys, clear=False), self.assertRaises(RuntimeError):
            model_config.build_models()

    def test_builds_only_configured_provider(self) -> None:
        assert model_config is not None
        keys = {
            "GEMINI_API_KEY": "test-key", "GROQ_API_KEY": "", "OPENROUTER_API_KEY": "",
            "SIDEKICK_PROVIDER_ORDER": "gemini,groq,openrouter", "SIDEKICK_GEMINI_MODELS": "test-model",
        }
        with patch.dict(os.environ, keys, clear=False):
            models = model_config.build_models()
        self.assertEqual(models.providers, ("gemini",))
        self.assertEqual(models.fallbacks, ())
        self.assertEqual(models.labels, ("gemini/test-model",))

    def test_configured_model_list_preserves_order_and_removes_duplicates(self) -> None:
        assert model_config is not None
        self.assertEqual(
            model_config.configured_models("SIDEKICK_TEST_MODELS", "TEST_MODEL", ("fallback",)),
            ("fallback",),
        )
        with patch.dict(os.environ, {"SIDEKICK_TEST_MODELS": "first, second, first"}):
            self.assertEqual(
                model_config.configured_models("SIDEKICK_TEST_MODELS", "TEST_MODEL", ("fallback",)),
                ("first", "second"),
            )


class StickyFallbackTests(unittest.IsolatedAsyncioTestCase):
    async def test_keeps_the_successful_fallback_for_the_next_model_call(self) -> None:
        from sidekick import StickyModelFallbackMiddleware

        primary, fallback = object(), object()
        middleware = StickyModelFallbackMiddleware(primary, fallback)
        attempted = []

        async def first_handler(model):
            attempted.append(model)
            if model is primary:
                raise RuntimeError("primary unavailable")
            return "fallback response"

        self.assertEqual(await middleware.awrap_model_call(RequestStub(), first_handler), "fallback response")
        self.assertEqual(attempted, [primary, fallback])

        attempted.clear()

        async def next_handler(model):
            attempted.append(model)
            return "continued response"

        self.assertEqual(await middleware.awrap_model_call(RequestStub(), next_handler), "continued response")
        self.assertEqual(attempted, [fallback])

    async def test_rate_limited_provider_is_skipped_for_the_rest_of_the_task(self) -> None:
        from sidekick import StickyModelFallbackMiddleware

        groq, openrouter = object(), object()
        middleware = StickyModelFallbackMiddleware(
            groq, openrouter, provider_names=("groq", "openrouter")
        )

        async def successful_groq(model):
            return "first response"

        await middleware.awrap_model_call(RequestStub(), successful_groq)

        class RateLimitError(Exception):
            status_code = 429

        attempted = []

        async def change_provider(model):
            attempted.append(model)
            if model is groq:
                raise RateLimitError("rate limit reached")
            return "openrouter response"

        self.assertEqual(await middleware.awrap_model_call(RequestStub(), change_provider), "openrouter response")
        self.assertEqual(attempted, [groq, openrouter])
        self.assertIn("groq", middleware.rate_limited_providers)

        attempted.clear()
        self.assertEqual(await middleware.awrap_model_call(RequestStub(), change_provider), "openrouter response")
        self.assertEqual(attempted, [openrouter])

    def test_cross_provider_messages_drop_reasoning_metadata(self) -> None:
        from langchain_core.messages import AIMessage
        from sidekick import cross_provider_messages

        original = AIMessage(
            content=[{"type": "reasoning", "text": "private chain"}, {"type": "text", "text": "answer"}],
            additional_kwargs={"reasoning_content": "private chain", "safe": "kept"},
        )
        normalized = cross_provider_messages([original])[0]

        self.assertEqual(normalized.content, [{"type": "text", "text": "answer"}])
        self.assertEqual(normalized.additional_kwargs, {"safe": "kept"})

    def test_recognizes_gemini_resource_exhausted_as_a_rate_limit(self) -> None:
        from sidekick import is_rate_limit_error

        class GoogleRateLimitError(Exception):
            pass

        self.assertTrue(is_rate_limit_error(GoogleRateLimitError("429 RESOURCE_EXHAUSTED: quota exceeded")))


class VisiblePlanTests(unittest.TestCase):
    def test_initial_plan_starts_with_one_active_item(self) -> None:
        from sidekick import initial_plan

        todos = initial_plan("Español")
        self.assertEqual(len(todos), 4)
        self.assertEqual([todo["status"] for todo in todos], ["in_progress", "pending", "pending", "pending"])

    def test_successful_plan_is_completed(self) -> None:
        from sidekick import complete_plan, initial_plan

        self.assertTrue(all(todo["status"] == "completed" for todo in complete_plan(initial_plan("English"))))

    def test_error_detail_redacts_configured_keys(self) -> None:
        from sidekick import safe_error_detail

        with patch.dict(os.environ, {"GEMINI_API_KEY": "private-token"}):
            detail = safe_error_detail(RuntimeError("provider rejected private-token"))
        self.assertNotIn("private-token", detail)
        self.assertIn("[redacted]", detail)

    def test_rejects_non_conventional_title(self) -> None:
        with self.assertRaises(ValueError):
            publish.validate("update documentation", "Describe the change.")

    def test_requires_both_manual_fields(self) -> None:
        with self.assertRaises(ValueError):
            publish.validate("fix: reject invalid metadata", None)

    def test_parses_json_wrapped_by_provider_text(self) -> None:
        self.assertEqual(
            publish.parse_proposal(
                'Result: {"title":"chore: automate repository checks",'
                '"description":"Add reusable verification."}'
            ),
            ("chore: automate repository checks", "Add reusable verification."),
        )


if __name__ == "__main__":
    unittest.main()
