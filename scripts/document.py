"""Generate repository documentation deterministically from local Git history."""

from __future__ import annotations

import argparse
import re
import subprocess
import unicodedata
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DECISIONS_DIR = ROOT / "docs" / "decisions"
CATEGORIES = (
    ("feat", "Features"), ("fix", "Fixes"), ("perf", "Performance"),
    ("refactor", "Refactors"), ("docs", "Documentation"),
    ("test", "Tests"), ("build", "Build"), ("ci", "CI"),
    ("chore", "Maintenance"), ("style", "Visual presentation"),
)
CONVENTIONAL = re.compile(
    rf"^({'|'.join(kind for kind, _ in CATEGORIES)})(?:\([^)]+\))?!?:\s+(.+)$",
    re.IGNORECASE,
)


def git(*args: str) -> str:
    return subprocess.run(
        ["git", "-c", f"safe.directory={ROOT.as_posix()}", "-C", str(ROOT), *args],
        check=True, capture_output=True, text=True, encoding="utf-8",
    ).stdout


def write_changelog() -> None:
    records: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for entry in git("log", "--pretty=format:%h%x1f%s%x1e").split("\x1e"):
        entry = entry.strip()
        if not entry or "\x1f" not in entry:
            continue
        commit_hash, subject = entry.split("\x1f", 1)
        match = CONVENTIONAL.match(subject)
        category = match.group(1).lower() if match else "other"
        description = match.group(2) if match else subject
        records[category].append((commit_hash, description))
    lines = [
        "# Changelog", "",
        "Generated deterministically from Git history with `python scripts/document.py changelog`.", "",
    ]
    for kind, heading in (*CATEGORIES, ("other", "Other changes")):
        if records[kind]:
            lines.extend([f"## {heading}", ""])
            lines.extend(f"- {subject} (`{commit_hash}`)" for commit_hash, subject in records[kind])
            lines.append("")
    (ROOT / "CHANGELOG.md").write_text("\n".join(lines), encoding="utf-8")
    print("CHANGELOG.md updated.")


def create_decision(title: str) -> None:
    slug = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
    if not slug:
        raise SystemExit("The title must contain letters or numbers.")
    numbers = [int(path.name[:4]) for path in DECISIONS_DIR.glob("[0-9][0-9][0-9][0-9]-*.md")]
    destination = DECISIONS_DIR / f"{max(numbers, default=0) + 1:04d}-{slug}.md"
    destination.write_text(
        f"# {title}\n\nDate: {date.today().isoformat()}\nStatus: proposed\n\n"
        "## Context\n\n<!-- Situation, constraints, and alternatives. -->\n\n"
        "## Decision\n\n<!-- Selected option and rationale. -->\n\n"
        "## Consequences\n\n<!-- Benefits, costs, risks, and follow-up work. -->\n",
        encoding="utf-8",
    )
    print(destination.relative_to(ROOT))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("changelog")
    decision = commands.add_parser("decision")
    decision.add_argument("title")
    arguments = parser.parse_args()
    write_changelog() if arguments.command == "changelog" else create_decision(arguments.title)


if __name__ == "__main__":
    main()
