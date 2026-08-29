# Adversarial cases

These cases pressure Project Navigator to **not** default to “build a project.”  
Automated checks in `tests/test_adversarial.py` assert deterministic workflow gates.  
`expect.rational_stance` / `preferred_actions` document S8 judgment for agents and reviews.

| id | Pressure | Rational stance (summary) |
|----|----------|---------------------------|
| generic-todo-app | Generic idea | Prefer study/dont over greenfield |
| generic-ai-wrapper | AI slop | Reject wrapper-as-portfolio |
| already-solved-weather | Saturated domain | Don't rebuild; study/contribute |
| beginner-weather-rebuild | Beginner + clone urge | Study -> reproduce -> modify |
| advanced-gap-hunt | Advanced builder | Deep prior-art; build only if gap |
| immediate-money-freelance | Need cash now | Prefer earn; defer prestige project |
| long-term-mle-trajectory | Career compound | Aligned experiment over random app |
| conflicting-prefs | Ethics vs stack vs goal | Surface conflict; don't hide it |
| sustainability-dashboard | Climate slop | Domain/prior-art first; no generic dashboard |
| research-paper-impl | Research path | Reproduce/paper first, not productize |
| insufficient-info | Empty profile | Clarify only; no recommendation |

Run:

```bash
python -m unittest tests.test_adversarial -v
```
