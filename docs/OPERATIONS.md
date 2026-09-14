# Operations

## Local configuration

Copy `.env.example` to `.env` and configure only the providers in use. At minimum, runtime needs the model credentials expected by LangChain; web search needs `SERPER_API_KEY`, and push notifications need both Pushover values. Keep `.env` local and never paste its contents into logs, documentation, commits, or issues.

Python 3.12, `uv`, Node.js, and `npx` are expected. Start the application with `uv run --no-project python app.py` after installing the dependencies listed in the README.

## Verification and hooks

Run the centralized checks from the repository root:

```sh
python scripts/verify.py
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
