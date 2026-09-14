"""Make one minimal request to every configured runtime model provider."""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from model_config import build_models  # noqa: E402


def main() -> int:
    load_dotenv(ROOT / ".env", override=True)
    configured = build_models()
    failed = False
    for provider, model in zip(configured.providers, (configured.primary, *configured.fallbacks)):
        try:
            response = model.invoke("Reply with exactly OK.")
            if not response.content:
                raise RuntimeError("empty response")
            print(f"[provider] {provider}: OK")
        except Exception as error:  # Provider SDKs expose different exception trees.
            failed = True
            print(f"[provider] {provider}: FAILED ({type(error).__name__})")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
