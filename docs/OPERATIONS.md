# Operations

## Local configuration

Copy `.env.example` to `.env` and configure only the providers in use. Runtime requires at least one of `GEMINI_API_KEY`, `GROQ_API_KEY`, or `OPENROUTER_API_KEY`; web search needs `SERPER_API_KEY`, and push notifications need both Pushover values. Keep `.env` local and never paste its contents into logs, documentation, commits, or issues.

Python 3.12, `uv`, Node.js, and `npx` are expected. Run `uv sync`, then start the application with `uv run python app.py`.

## Models and observability

`SIDEKICK_PROVIDER_ORDER` controls runtime priority and defaults to `gemini,groq,openrouter`. Providers without credentials are skipped. `GEMINI_MODEL`, `GROQ_MODEL`, and `OPENROUTER_MODEL` select models independently. Both the tool-using worker and structured evaluator use the resulting fallback chain.

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

Run `python scripts/publish.py` only after the user explicitly authorizes committing and pushing. The command lists included changes, verifies them, proposes an English Conventional Commit title and description, and requires typing `PUBLISH` before staging, re-verifying, committing, and pushing the current branch to `origin`. It never force-pushes.

Proposal fallback order is Gemini, Groq, then OpenRouter, using credentials from the ignored `.env`. Override models with `GEMINI_COMMIT_MODELS`, `GROQ_COMMIT_MODEL`, or `OPENROUTER_COMMIT_MODEL`; override the 15-second request timeout with `COMMIT_GENERATION_TIMEOUT`. To avoid external generation, pass both `--title` and `--description`.

If verification fails after staging, fix the reported problem and rerun verification. The command does not discard changes or rewrite history.
