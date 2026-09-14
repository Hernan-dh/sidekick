# Architecture

## Overview

Sidekick is a Gradio application around a LangChain agent compiled as a LangGraph and a separate structured evaluator. The worker attempts each task, exposes its plan to the UI, pauses before sensitive tools, and may retry from evaluator feedback. LangSmith can trace the complete graph and provider calls when enabled.

```text
Gradio UI -> Sidekick orchestration -> LangChain worker -> local/MCP tools
                           |            |
                           |            +-> Gemini -> Groq -> OpenRouter fallback
                           +-> structured evaluator -> accept, retry, or ask user
                                        |
                                        +-> same provider fallback
```

## Components

- `app.py`: Gradio lifecycle, chat, approval, reset, and live plan panel.
- `styles.py`: shared chatbot typography and responsive light/dark color themes.
- `sidekick.py`: worker/evaluator loop, middleware, checkpoints, retry budget, and approval resume.
- `model_config.py`: provider construction, ordering, and fallback configuration.
- `sidekick_tools.py`: Serper and Wikipedia tools, Pushover notification, and persistent Playwright/filesystem MCP sessions.
- `slide_kit.py`: PowerPoint generation helper for the sandbox skill assets.
- `scripts/`: deterministic documentation, centralized verification, hook installation, and human-confirmed publication.

## Data and trust boundaries

User requests, success criteria, model replies, and tool results enter the selected external model API. Search queries go to Serper; notifications go to Pushover; browser activity reaches visited sites. Playwright can interact with external pages, while the filesystem MCP server is restricted to `sandbox/`. When LangSmith tracing is enabled, prompts, responses, graph steps, tool metadata, timings, and errors are also sent to LangSmith.

The local `.env` contains credentials and is ignored. Generated sandbox content is ignored. Commit proposal generation sends only a bounded list of changed paths, tracked diffs, and readable new files; repository content is explicitly treated as untrusted data.

## Safety controls

PII middleware filters email and credit-card data in configured paths, model calls have a per-run limit, provider failures advance through the configured fallback chain, and notification or human-help actions pause for approval. Publication separately requires repository verification and an explicit `PUBLISH` confirmation; it never force-pushes.

## Interface localization and themes

The browser language selects Spanish or English on first load; the user can change it at any time. Interface labels, plan placeholders, approval status, evaluator labels, and the worker's response-language instruction follow that selection. Theme preference is independent, follows the operating-system preference initially, and is persisted in browser local storage. Both palettes use the same Manrope/DM Mono typography and geometric visual system as the other chatbot interfaces.
