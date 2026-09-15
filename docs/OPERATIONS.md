# Operations

## Local configuration

Copy `.env.example` to `.env` and configure only the providers in use. Runtime requires at least one of `GEMINI_API_KEY`, `GROQ_API_KEY`, or `OPENROUTER_API_KEY`. DDGS web search needs no key; `SERPER_API_KEY` additionally enables Google results through Serper, and push notifications need both Pushover values. `DDGS_REGION` and `DDGS_BACKEND` are optional metasearch settings. Keep `.env` local and never paste its contents into logs, documentation, commits, or issues.

Python 3.12, `uv`, Node.js, and `npx` are expected. Run `uv sync`, then start the application with `uv run python app.py`.

The interface detects Spanish or English from the browser and exposes a manual language selector. The theme button switches between light and dark palettes; the selection is stored locally in the browser. Clearing site storage resets the theme to the operating-system preference.

## Models and observability

`SIDEKICK_PROVIDER_ORDER` controls runtime priority and defaults to `gemini,groq,openrouter`. Providers without credentials are skipped. `SIDEKICK_GEMINI_MODELS`, `SIDEKICK_GROQ_MODELS`, and `SIDEKICK_OPENROUTER_MODELS` define each provider's comma-separated model chain. The legacy singular settings (`GEMINI_MODEL`, `GROQ_MODEL`, and `OPENROUTER_MODEL`) remain supported and are placed before that provider's defaults. Both the tool-using worker and structured evaluator use the resulting fallback chain.

Sidekick does not impose a time budget or model-call limit on a task. It continues until it completes, needs human input, or a provider/tool returns an actual error. The status below the workspace reports the active phase, current tool when known, and elapsed time. Individual network requests retain their own short timeout so a disconnected service cannot freeze the application. The model receives a compact set of browser and sandbox operations rather than every MCP tool schema, keeping requests below provider input-token allowances.

Gemini may log that it ignores `$schema` or `additionalProperties` from MCP tool definitions: it safely reduces those schemas to the Gemini-supported subset. Sidekick keeps the provider that successfully takes over for the remainder of a task, minimizing cross-provider message conversion. On a provider change, Sidekick removes provider-native reasoning metadata but preserves text, tool-call IDs, and graph state. A 429/rate-limit response excludes that provider for the remainder of the active task and immediately advances to the next configured provider. Check Groq's organization Limits page, Google AI Studio, and the OpenRouter key page for the account-specific quotas in effect.

LangSmith is optional. Add `LANGSMITH_API_KEY`, set `LANGSMITH_TRACING=true`, and optionally change `LANGSMITH_PROJECT` (default `sidekick`). Traces can contain prompts, responses, and tool data; leave tracing disabled for sensitive workloads that must not reach LangSmith.

Validate every configured provider with one minimal request:

```sh
uv run python scripts/check_providers.py
```

Validate graph construction and MCP startup without serving Gradio:

```sh
uv run python scripts/smoke_test.py
```

## Verification and hooks

Run the centralized checks from the repository root:

```sh
uv run python scripts/verify.py
# or on Linux/macOS/Git Bash
./scripts/verify.sh
```

The verifier checks whitespace, Python syntax, essential documentation, ignored/generated/private files, and likely secrets. If tests exist, it runs the standard-library unittest suite. GitHub Actions runs the same verifier on pushes and pull requests.

Enable the versioned pre-commit hook once per clone:

```sh
python scripts/install_hooks.py
```

## Continuous documentation

Rebuild the changelog from local Git history or create the next numbered ADR draft:

```sh
python scripts/document.py changelog
python scripts/document.py decision "Decision title"
```

Update architecture and operations documentation in the same change whenever their subject changes. ADRs are for durable choices with meaningful alternatives, not daily activity logs.

## Commit publication

Preview verification and generated Conventional Commit metadata without staging files:

```sh
python scripts/publish.py --preview
```

Run `python scripts/publish.py` only after the user explicitly authorizes committing and pushing. The command lists included changes, verifies them, proposes an English Conventional Commit title and description, and prints that proposal again immediately above the `PUBLISH` prompt. It requires typing `PUBLISH` before staging, re-verifying, committing, and pushing the current branch to `origin`. It never force-pushes.

Proposal fallback order is Gemini, Groq, then OpenRouter, using credentials from the ignored `.env`. Override models with `GEMINI_COMMIT_MODELS`, `GROQ_COMMIT_MODEL`, or `OPENROUTER_COMMIT_MODEL`; override the 15-second request timeout with `COMMIT_GENERATION_TIMEOUT`. To avoid external generation, pass both `--title` and `--description`.

If verification fails after staging, fix the reported problem and rerun verification. The command does not discard changes or rewrite history.
