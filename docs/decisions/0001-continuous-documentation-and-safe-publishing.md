# Continuous documentation and safe publishing

Date: 2026-09-14
Status: accepted

## Context

Sidekick integrates model, search, browser, filesystem, and notification services and therefore evolves across several trust boundaries. Its repository also contains local provider credentials. Technical decisions and publication checks need to remain repeatable without depending on external conversations.

## Decision

Adopt the documentation and publishing pattern used by the Python agent repositories: keep architecture, operations, and ADRs versioned; generate the changelog and ADR drafts deterministically; centralize dependency-free verification for local use, a repository-managed pre-commit hook, and GitHub Actions; and provide an AI-assisted publication command that requires explicit human confirmation.

Commit proposals use bounded repository context and a Gemini-to-Groq-to-OpenRouter fallback. Manual metadata remains available when changes should not be sent to a provider.

## Consequences

- Lasting behavior and operational knowledge change with the code.
- Local commits and CI share the same checks.
- Credentials and common generated artifacts are rejected before publication.
- Publishing remains a deliberate human action and never force-pushes.
- Contributors must enable the hook once per clone and maintain documentation alongside relevant changes.
