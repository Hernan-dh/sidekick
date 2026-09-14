# Agent instructions

## Continuous documentation

- Document lasting functional, technical, or operational decisions in the same task.
- Organize documentation by topic and decision; do not create daily logs.
- Update `docs/ARCHITECTURE.md` when components, integrations, trust boundaries, or data flows change.
- Update `docs/OPERATIONS.md` when configuration, execution, verification, diagnostics, or recovery changes.
- Create an ADR in `docs/decisions/` only when relevant alternatives exist and the decision is not evident from the code.
- Do not document cosmetic changes, trivial fixes, or refactors without behavioral changes.
- Never include tokens, credentials, `.env` values, personal data, or private information in versioned files or diagnostic output.
- State in the final response which documentation was created or updated, or explicitly say that the change had no documentation impact.

## Publishing

- Run `./scripts/verify.sh` before proposing publication.
- Use Conventional Commits in English, with titles no longer than 72 characters.
- Do not create commits or push without explicit user authorization.
- Never force-push.
