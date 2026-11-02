# Project Navigator Skill 2.0

Version `2.0.0`, derived from Skill 1.x commit `9026097`. This isolated Skill 2.0 implementation includes workflow, retrieval, and validation improvements; the original v1 source remains unchanged.

Project Navigator is a decision-support skill for a host AI agent.

It helps answer:

- what the user should work on next;
- whether an idea is worth pursuing;
- whether something already exists;
- what the real gap is;
- whether to build, research, learn, contribute, reframe, defer, or drop;
- what the smallest useful next experiment is.

This repository is the canonical implementation for the skill package.

## What this repository contains

Runtime/core:

- `SKILL.md` — the authoritative entry point for the host agent
- `prompts/` — policy and stage prompts
- `templates/` — user profile and recommendation contract
- `scripts/` — validation and workflow helpers
- `retrieval/` — host-search protocol and evidence handling
- `schemas/` — JSON contracts

Documentation:

- `README.md`
- `QUICKSTART.md`
- `VISION.md`
- `MERGE.md`
- `RELEASE_NOTES.md`

Examples + development:

- `examples/`
- `tests/`
- `evaluations/`

## Install and usage

Copy the repository into the supported skills directory for your host. The folder should be named `project-navigator`.

Typical host examples:

- `~/.cursor/skills/project-navigator/`
- `~/.claude/skills/project-navigator/`
- `~/.codex/skills/project-navigator/`
- `~/.github/skills/project-navigator/`

No backend, no database, no API key, and no proprietary search backend are required. The host agent must provide search tools when research is needed.

## Conversation pattern

A typical agent flow is:

1. ask for clarification if the request is under-specified;
2. extract objective and constraints;
3. decide whether prior-art search is worth the cost;
4. if needed, use host search tools and normalize evidence;
5. identify the real gap and fit for the user;
6. recommend one action and validate the result.

## Local validation

```bash
python -m unittest discover -s tests -v
python scripts/validate_profile.py --profile examples/sample-profile.md
python scripts/check_recommendation.py --in examples/sample-recommendation.md --retrieval-status NOT_SEARCHED
python scripts/run_preflight.py --profile examples/sample-profile.md --question "What should I work on this month?" --mode quick
```

## Design intent

The system is designed to improve decision quality, not to generate endless project ideas. It should favor study, contribution, extension, and the smallest meaningful experiment over blind greenfield builds.

For the full operating guidance, see [SKILL.md](SKILL.md) and [QUICKSTART.md](QUICKSTART.md).
