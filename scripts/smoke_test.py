"""Start Sidekick's graph and MCP tools, then shut them down without serving the UI."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sidekick import Sidekick  # noqa: E402


async def smoke_test() -> None:
    sidekick = Sidekick()
    try:
        await sidekick.setup()
        print(f"Sidekick graph ready with providers: {', '.join(sidekick.providers)}")
        print(f"Loaded tools: {len(sidekick.tools)}")
    finally:
        sidekick.cleanup()
        if sidekick.sessions and sidekick.sessions._task:
            await sidekick.sessions._task


if __name__ == "__main__":
    asyncio.run(smoke_test())
