# Architecture

## Overview

Sidekick is a Gradio application around a LangChain agent and a separate structured evaluator. The worker attempts each task, exposes its plan to the UI, pauses before sensitive tools, and may retry from evaluator feedback.

```text
Gradio UI -> Sidekick orchestration -> LangChain worker -> local/MCP tools
                           |
                           +-> structured evaluator -> accept, retry, or ask user
```

## Components

- `app.py`: Gradio lifecycle, chat, approval, reset, and live plan panel.
- `sidekick.py`: worker/evaluator loop, middleware, checkpoints, retry budget, and approval resume.
- `sidekick_tools.py`: Serper and Wikipedia tools, Pushover notification, and persistent Playwright/filesystem MCP sessions.
- `styles.py`: UI theme and presentation.
- `slide_kit.py`: PowerPoint generation helper for the sandbox skill assets.
- `scripts/`: deterministic documentation, centralized verification, hook installation, and human-confirmed publication.

## Data and trust boundaries

User requests, success criteria, model replies, and tool results enter external model APIs. Search queries go to Serper; notifications go to Pushover; browser activity reaches visited sites. Playwright can interact with external pages, while the filesystem MCP server is restricted to `sandbox/`.

The local `.env` contains credentials and is ignored. Generated sandbox content is ignored. Commit proposal generation sends only a bounded list of changed paths, tracked diffs, and readable new files; repository content is explicitly treated as untrusted data.

## Safety controls

PII middleware filters email and credit-card data in configured paths, model calls have a per-run limit, and notification or human-help actions pause for approval. Publication separately requires repository verification and an explicit `PUBLISH` confirmation; it never force-pushes.
