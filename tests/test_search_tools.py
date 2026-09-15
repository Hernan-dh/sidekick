"""Tests for compact, safe DDGS search result formatting."""

import json
import unittest

from sidekick_tools import _format_ddgs_results, select_agent_tools


class DdgsToolTests(unittest.TestCase):
    def test_formats_only_agent_relevant_fields_and_limits_results(self) -> None:
        results = [
            {"title": f"Result {number}", "href": f"https://example.com/{number}", "body": "Summary", "extra": "skip"}
            for number in range(6)
        ]
        formatted = json.loads(_format_ddgs_results(results))
        self.assertEqual(len(formatted), 5)
        self.assertEqual(formatted[0], {"title": "Result 0", "url": "https://example.com/0", "snippet": "Summary"})

    def test_exposes_only_compact_mcp_operations_to_the_agent(self) -> None:
        class Tool:
            def __init__(self, name: str) -> None:
                self.name = name

        selected = select_agent_tools([Tool("browser_navigate"), Tool("browser_evaluate"), Tool("read_file")])

        self.assertEqual([tool.name for tool in selected], ["browser_navigate", "read_file"])


if __name__ == "__main__":
    unittest.main()
