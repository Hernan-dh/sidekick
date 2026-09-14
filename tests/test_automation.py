"""Regression tests for the dependency-free repository automation."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


publish = load_script("publish")


class PublishMetadataTests(unittest.TestCase):
    def test_accepts_conventional_metadata(self) -> None:
        self.assertEqual(
            publish.validate("docs: explain publishing", "Document the safe publication workflow."),
            ("docs: explain publishing", "Document the safe publication workflow."),
        )

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
