# Profile resolution

Resolve the user's working profile from any host-provided context without fabricating facts.

## Inputs

- conversation history if available
- persistent memory if available
- current conversation text
- host context and profile snapshots

## Rules

- Prefer explicit, newer information over older or inferred information.
- Before asking questions, extract explicit profile facts from the current request and merge them as recent conversation data.
- Reuse facts stated in the request (such as coding level, interests, objective, or time budget); do not infer facts from vague wording.
- Mark inferred facts with lower confidence.
- Do not ask for a full profile questionnaire unless the missing information materially affects the decision.
- Keep personal data in runtime memory only; do not write it into repo fixtures or public artifacts.
- If local opportunity research is relevant, require country first; request city or region only when it materially changes the answer.

## Output

A normalized profile containing the strongest available evidence for:

- objectives and constraints
- skills and capacity
- interests and domains
- location and local-market relevance
- working preferences and risk tolerance

Keep the profile structured, evidence-aware, and minimal for the decision at hand.
