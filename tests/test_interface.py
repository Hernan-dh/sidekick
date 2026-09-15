"""Tests for Sidekick interface localization and themes."""

import unittest
from types import SimpleNamespace

import app


class InterfaceTests(unittest.TestCase):
    def test_detects_spanish_browser_language(self) -> None:
        self.assertEqual(app.initialize_language("es-AR"), "Español")

    def test_defaults_other_browser_languages_to_english(self) -> None:
        self.assertEqual(app.initialize_language("pt-BR"), "English")

    def test_header_is_localized(self) -> None:
        self.assertIn("Tu compañero de trabajo personal", app.header_html("Español"))
        self.assertIn("Your personal coworker", app.header_html("English"))

    def test_plan_escapes_untrusted_content(self) -> None:
        rendered = app.render_todos([{"status": "pending", "content": "<script>"}], "English")
        self.assertIn("&lt;script&gt;", rendered)
        self.assertNotIn("<script>", rendered)

    def test_theme_toggle_is_available(self) -> None:
        self.assertIn("toggleSidekickTheme", app.styles.JS)
        self.assertIn("data-sidekick-theme", app.styles.CSS)

    def test_status_reports_active_tool_without_exposing_html(self) -> None:
        sidekick = SimpleNamespace(activity="tool:web_search", started_at=None)

        rendered = app.render_status(sidekick, "English")

        self.assertIn("Using web search", rendered)
        self.assertIn("work-status", rendered)


if __name__ == "__main__":
    unittest.main()
