# Sidekick

A personal AI coworker with a Gradio interface, an evaluator loop, web and filesystem tools, live planning, and human approval for sensitive actions.

## Run locally

Python 3.12 and `uv` are the development baseline. Synchronize the locked environment, then copy `.env.example` to `.env` and replace only the required placeholders. Never commit `.env`.

```sh
uv sync
uv run python app.py
```

The browser and sandbox filesystem tools start through `npx`, so Node.js must also be available.

Sidekick uses the configured providers in `SIDEKICK_PROVIDER_ORDER` (Gemini, Groq, then OpenRouter by default), skipping providers without keys and falling back when a model request fails. Add `LANGSMITH_API_KEY` and set `LANGSMITH_TRACING=true` to record LangChain/LangGraph traces in the `sidekick` project.

## Documentation and publication

Architecture and trust boundaries are described in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). Configuration, verification, documentation generation, and safe publication are described in [docs/OPERATIONS.md](docs/OPERATIONS.md).

```sh
python scripts/document.py changelog
python scripts/document.py decision "Decision title"
python scripts/install_hooks.py
python scripts/publish.py --preview
```

The publication command never commits or pushes without the literal `PUBLISH` confirmation. Supplying `--title` and `--description` avoids sending a bounded change context to an external model.
