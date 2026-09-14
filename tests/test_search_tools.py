"""Tests for compact, safe DDGS search result formatting."""

import json
import unittest

from sidekick_tools import _format_ddgs_results


class DdgsToolTests(unittest.TestCase):
    def test_formats_only_agent_relevant_fields_and_limits_results(self) -> None:
        results = [
            {"title": f"Result {number}", "href": f"https://example.com/{number}", "body": "Summary", "extra": "skip"}
            for number in range(6)
        ]
        formatted = json.loads(_format_ddgs_results(results))
        self.assertEqual(len(formatted), 5)
        self.assertEqual(formatted[0], {"title": "Result 0", "url": "https://example.com/0", "snippet": "Summary"})


if __name__ == "__main__":
    unittest.main()
