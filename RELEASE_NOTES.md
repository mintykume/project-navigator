# Project Navigator 2.0.0

Project Navigator 2.0.0 is a standalone, host-neutral decision-support skill. It helps a host agent decide whether to build, research, learn, contribute, reframe, defer, or drop an idea, and to identify a useful next experiment.

## Completed hardening

- **P0:** Research-intent and quick/deep workflow gates; profile fact extraction; explicit retrieval states for unsearched, zero-result, usable-result, and unusable-evidence outcomes.
- **P1:** Recommendation contract linting; retrieved content is sanitized and treated as untrusted evidence; strict source-domain classification; relevance and evidence-quality filtering.
- **P2:** Conservative URL canonicalization; tolerant profile-field parsing; placeholder handling; structured opportunity/location context; relevance-first retrieval ranking; clarified retrieval-state semantics; fail-fast evaluation-profile validation.
- **P3:** Recommendation heading/action tolerance; search-keyword cleanup for filler and terminal punctuation, technical tokens, and Unicode words; GitHub look-alike domains are handled by strict hostname matching.

## Architecture

The package contains the host-agent workflow prompts, profile and recommendation templates, JSON schemas, deterministic Python scripts, examples, tests, and evaluation cases. Runtime scripts use Python's standard library and local modules. Search is supplied by the host agent; no proprietary search backend, database, API key, or extra Python package is required.

The workflow distinguishes `NOT_SEARCHED`, `SEARCHED_WITH_RESULTS`, `SEARCHED_NO_RESULTS`, and `SEARCHED_NO_USABLE_EVIDENCE`. Retrieved text is sanitized and labeled as untrusted evidence. Recommendations are checked with `scripts/check_recommendation.py`.

## Verification

- Unit tests: **153 passed**.
- Deterministic evaluation harness: **8 cases completed**. The harness exits successfully; quick-path cases intentionally stop at `awaiting_research_decision`, while deep-path cases reach `ready`.
- The unavailable original 61-check battery was not rerun and is not claimed as verified.

## Known limitations

- The original definitions for P2-1, P2-2, and P2-3 were unavailable in the source QA report/repository history used for this audit. Their exact mapping to later fixes cannot be independently verified; no duplicate fixes were invented.
- The evaluation harness uses the same retrieval fixture for all eight cases, although it is unrelated to most case questions. It validates workflow integration and status handling, not realistic case-specific retrieval or final recommendation quality.
- Live retrieval remains the host agent's responsibility.
- English-language research-intent and search-query heuristics are deterministic and are not a general multilingual NLP system.

Skill 2.0.0 is isolated under `tba/`. The original Skill 1.x repository remains unchanged at commit `90260978ceab5f79879a007bee7d732a212e0a90`.
