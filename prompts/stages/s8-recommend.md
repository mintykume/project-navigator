# S8 -- Recommend

**Goal:** One structured recommendation after S1-S7. Single synthesis call.

Use the context pack + notes from prior stages. Load `templates/decision-output.md`.

## Choose action

`build` | `study` | `reproduce` | `contribute` | `extend` | `research` | `earn` | `network` | `wait` | `dont`

Default to the **cheapest useful experiment** with a clear success condition -- not a full build.

## Rationality filter (before locking)

1. Real problem? User need it?
2. Equivalent exist? Why another implementation?
3. Demand or learning value?
4. Fit trajectory + constraints? Opportunity cost?
5. Smaller experiment available?
6. Still rational if AI hadn't made coding cheap?
7. Impressive-sounding only? -> reject

Weak answers -> downgrade action or **dont**.

## Confidence

Separate Known / Inferred / Unknown. If S4 skipped, prior art is Unknown (unless not applicable).

## Next

S9: `python scripts/check_recommendation.py --in <draft>` -- one repair pass if lint fails.
