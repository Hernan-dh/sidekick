"""Run dependency-free repository verification locally, in Git hooks, and in CI."""

from __future__ import annotations

import ast
import os
import re
import subprocess
import sys
import tokenize
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GIT = ["git", "-c", f"safe.directory={ROOT.as_posix()}", "-C", str(ROOT)]
REQUIRED = (
    "README.md", "AGENTS.md", ".env.example", "CHANGELOG.md",
    "docs/ARCHITECTURE.md", "docs/OPERATIONS.md", "docs/decisions/README.md",
)
PRIVATE_NAMES = {".env", "credentials.json", "secrets.json", "secrets.yaml", "id_rsa", "id_ed25519"}
PRIVATE_SUFFIXES = {".key", ".pem", ".p12", ".pfx"}
GENERATED_PARTS = {".venv", "venv", "__pycache__", ".pytest_cache", "node_modules", "sandbox", ".playwright-mcp"}
TEXT_SUFFIXES = {".css", ".env", ".html", ".ini", ".js", ".json", ".md", ".py", ".sh", ".toml", ".txt", ".yaml", ".yml"}
TEXT_NAMES = {".env.example", ".gitattributes", ".gitignore", "AGENTS.md", "Dockerfile", "pre-commit"}
SECRET_PATTERNS = (
    re.compile(r"AIza[0-9A-Za-z_-]{35}"),
    re.compile(r"\b(?:gsk_|github_pat_|sk-or-v1-)[A-Za-z0-9_-]{20,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[opurs]_[A-Za-z0-9_]{30,}\b"),
    re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"(?i)\b(?:api[_-]?key|secret|token|password)\b\s*[:=]\s*[\"']?([^\s\"'#]{12,})"),
)
PLACEHOLDERS = ("your-", "your_", "example", "placeholder", "change-me", "changeme")


class Verification:
    def __init__(self) -> None:
        self.errors: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def run(self, label: str, command: list[str]) -> None:
        print(f"[check] {label}")
        if subprocess.run(command, cwd=ROOT).returncode:
            self.error(f"{label} failed")


def repository_files(checks: Verification) -> list[Path]:
    result = subprocess.run(
        [*GIT, "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        capture_output=True,
    )
    if result.returncode:
        checks.error("Could not list repository files")
        return []
    return [ROOT / item.decode("utf-8") for item in result.stdout.split(b"\0") if item]


def check_python(checks: Verification, files: list[Path]) -> None:
    print("[check] Python syntax")
    for path in files:
        if path.suffix != ".py" or not path.is_file():
            continue
        try:
            with tokenize.open(path) as source:
                ast.parse(source.read(), filename=str(path))
        except (SyntaxError, UnicodeError) as error:
            checks.error(f"Invalid Python syntax in {path.relative_to(ROOT)}: {error}")


def check_files(checks: Verification, files: list[Path]) -> None:
    print("[check] private, generated, large files, and potential secrets")
    for path in files:
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        parts = {part.lower() for part in relative.parts}
        if path.name.lower() in PRIVATE_NAMES or (path.name.startswith(".env.") and path.name != ".env.example") or path.suffix.lower() in PRIVATE_SUFFIXES:
            checks.error(f"Private file is not allowed: {relative}")
        if parts & GENERATED_PARTS:
            checks.error(f"Generated file is not ignored: {relative}")
        if path.stat().st_size > 5 * 1024 * 1024:
            checks.error(f"File exceeds 5 MiB: {relative}")
        if path.stat().st_size > 1024 * 1024 or (path.suffix.lower() not in TEXT_SUFFIXES and path.name not in TEXT_NAMES):
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for number, line in enumerate(lines, 1):
            for pattern in SECRET_PATTERNS:
                match = pattern.search(line)
                if not match:
                    continue
                candidate = (match.group(1) if match.lastindex else "").lower()
                if candidate.startswith(PLACEHOLDERS) or (candidate and re.fullmatch(r"[a-z][a-z0-9_]+", candidate, re.I)):
                    continue
                checks.error(f"Sensitive value candidate at {relative}:{number}")
                break


def main() -> int:
    checks = Verification()
    files = repository_files(checks)
    checks.run("git diff --check", [*GIT, "--no-pager", "diff", "--check"])
    checks.run("git diff --cached --check", [*GIT, "--no-pager", "diff", "--cached", "--check"])
    print("[check] essential documentation")
    for relative in REQUIRED:
        if not (ROOT / relative).is_file():
            checks.error(f"Missing essential documentation: {relative}")
    check_python(checks, files)
    check_files(checks, files)
    if (ROOT / "uv.lock").is_file() and not os.getenv("CI"):
        checks.run("locked dependencies", ["uv", "lock", "--check"])
    tests = [path for path in files if path.name.startswith("test_") and path.suffix == ".py"]
    if tests:
        test_python = ["uv", "run", "python"] if (ROOT / "uv.lock").is_file() else [sys.executable]
        checks.run("tests", [*test_python, "-m", "unittest", "discover", "-s", "tests", "-v"])
    else:
        print("[check] tests (none discovered; skipped)")
    if checks.errors:
        print("\nVerification failed:")
        for error in checks.errors:
            print(f"- {error}")
        return 1
    print("\nVerification completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
