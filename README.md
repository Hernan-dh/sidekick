# Sidekick

A personal AI coworker with a Gradio interface, an evaluator loop, web and filesystem tools, live planning, and human approval for sensitive actions.

## Run locally

Python 3.12 and `uv` are the development baseline. Create the environment and install the application dependencies, then copy `.env.example` to `.env` and replace only the required placeholders. Never commit `.env`.

```sh
uv venv --python 3.12
uv pip install gradio langchain langchain-openai langchain-community langchain-mcp-adapters langgraph python-dotenv requests wikipedia python-pptx
uv run --no-project python app.py
```

The browser and sandbox filesystem tools start through `npx`, so Node.js must also be available.

## Documentation and publication

Architecture and trust boundaries are described in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). Configuration, verification, documentation generation, and safe publication are described in [docs/OPERATIONS.md](docs/OPERATIONS.md).

```sh
python scripts/document.py changelog
python scripts/document.py decision "Decision title"
python scripts/install_hooks.py
python scripts/publish.py --preview
```

The publication command never commits or pushes without the literal `PUBLISH` confirmation. Supplying `--title` and `--description` avoids sending a bounded change context to an external model.
