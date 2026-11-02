# S1 -- Clarify

**Goal:** Decide if clarification is required before any evaluation.

1. Run `python scripts/run_preflight.py` or `python scripts/missing_fields.py --critical-only --profile …`.
2. Preflight resolves explicit facts from the current user question before listing missing fields.
3. If `needs_clarification`: ask **only** the still-missing returned bank questions from `templates/clarifying-questions.md` (max 1-3). **STOP.**
4. Else: note optional gaps for Confidence later. Continue to S2.

Do not invent quiz questions, search the web, or recommend yet.

Critical fields: `primary_objective`, `time_budget`, and at least one capability list with content.
