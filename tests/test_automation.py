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
            "SIDEKICK_PROVIDER_ORDER": "gemini,groq,openrouter",
        }
        with patch.dict(os.environ, keys, clear=False), self.assertRaises(RuntimeError):
            model_config.build_models()

    def test_builds_only_configured_provider(self) -> None:
        assert model_config is not None
        keys = {
            "GEMINI_API_KEY": "test-key", "GROQ_API_KEY": "", "OPENROUTER_API_KEY": "",
            "SIDEKICK_PROVIDER_ORDER": "gemini,groq,openrouter",
        }
        with patch.dict(os.environ, keys, clear=False):
            models = model_config.build_models()
        self.assertEqual(models.providers, ("gemini",))
        self.assertEqual(models.fallbacks, ())


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


class VisiblePlanTests(unittest.TestCase):
    def test_initial_plan_starts_with_one_active_item(self) -> None:
        from sidekick import initial_plan

        todos = initial_plan("Español")
        self.assertEqual(len(todos), 4)
        self.assertEqual([todo["status"] for todo in todos], ["in_progress", "pending", "pending", "pending"])

    def test_successful_plan_is_completed(self) -> None:
        from sidekick import complete_plan, initial_plan

        self.assertTrue(all(todo["status"] == "completed" for todo in complete_plan(initial_plan("English"))))

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
