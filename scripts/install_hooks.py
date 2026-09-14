"""Enable the repository-managed Git hooks for this clone."""

import stat
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / ".githooks" / "pre-commit"
GIT = ["git", "-c", f"safe.directory={ROOT.as_posix()}", "-C", str(ROOT)]

HOOK.chmod(HOOK.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
subprocess.run([*GIT, "config", "core.hooksPath", ".githooks"], check=True)
print("Hooks enabled for this clone: .githooks")
