# Canonicalization note

This repository is the canonical Project Navigator codebase for future development.

## Why this is canonical

This repository is the stronger engineering foundation because it already contains the operational pieces needed to run the Project Navigator workflow end-to-end:

- `retrieval/` adapters and query packs for existing-work search
- `schemas/` JSON contracts for profiles, recommendations, and retrieval briefs
- `scripts/` deterministic workflow logic for validation, context assembly, preflight, query generation, and retrieval normalization
- `tests/` coverage including adversarial cases, profile validation, and retrieval normalization checks

The codebase is already structured as a usable agent skill and has passed the current validation suite.

## What came from the historical repository

The historical repository contains a largely duplicate implementation of the core Project Navigator logic, but with one materially useful addition:

- `VISION.md` — a detailed human-facing philosophy document explaining why the system exists, what trade-offs it makes, and the anti-slop design rationale

That document has been copied into this repository as `VISION.md` so the canonical codebase retains the human rationale without depending on the historical repository.

## Duplicate directories/files

The following parts are effectively duplicates of the same core system and should be treated as historical/reference material unless explicitly needed:

- `README.md`
- `QUICKSTART.md`
- `SKILL.md`
- `prompts/`
- `templates/`
- `examples/`
- `scripts/`
- `tests/`

These files and directories reflect the same Project Navigator implementation in both repositories. The canonical repository keeps the more complete engineering version.

## Repository status

- Canonical repository for new work: this repository
- Historical/reference repository: kept out of active development unless explicitly needed for comparison

The historical repository should not be used as the active development target unless there is a specific need to compare historical design intent or recover an earlier version of a document. It should remain untouched as a reference copy.

## Development rule

Future work should happen only in the canonical repository unless there is an explicit, justified reason to inspect the historical copy. This keeps the project from splitting into two implementations.
