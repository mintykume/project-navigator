# Quick start

Project Navigator is a decision-support agent skill. It helps a host AI agent decide whether a project is worth pursuing, whether it already exists, what the actual gap is, and what the smallest useful next experiment should be.

It is not a generic idea generator and it does not replace the host agent's search tools.

## 1. Install the skill

Copy the repository into a skills directory supported by your host agent. Common examples:

- `~/.cursor/skills/project-navigator/`
- `~/.claude/skills/project-navigator/`
- `~/.codex/skills/project-navigator/`
- `~/.github/skills/project-navigator/`

You may also place it in a project-local equivalent if your host supports that. The folder name should be `project-navigator`.

The repository is already portable and does not require a database, a backend, an API key, or extra Python packages.

## 2. What the host agent needs

The host agent should provide:

- user conversation;
- LLM reasoning;
- search tools (web / GitHub / academic / other host-provided tools when available);
- filesystem access when available.

Project Navigator does not implement its own search backend. It expects the host to do external evidence gathering.

## 3. Provide a profile

The clearest path is to copy the sample profile and edit it:

```bash
cp examples/sample-profile.md my-profile.md
# then edit my-profile.md
```

You can also work from `templates/user-profile.md`.

## 4. Start a conversation

Try a prompt like:

```text
Using project-navigator, what should I work on next?
```

Or:

```text
Using my-profile.md and project-navigator, should I build an AI tutor for students?
```

The host should follow the S1-S9 workflow and ask only the targeted clarification questions when needed.

## 5. Research handling

If prior-art research is justified, the host agent should:

1. ask whether the user wants a quick answer or a deeper prior-art check;
2. rerun `run_preflight.py` with the same profile/question and `--research-decision quick` or `--research-decision deep`;
3. if the choice was deep, run the generated retrieval brief or search queries;
4. normalize the results with the original question, including an empty hit list; `NOT_SEARCHED`, `SEARCHED_WITH_RESULTS`, `SEARCHED_NO_RESULTS`, and `SEARCHED_NO_USABLE_EVIDENCE` remain distinct; retrieved text is sanitized and labeled as untrusted evidence in the context pack;
5. re-run preflight with the evidence.

When preflight receives either completed-empty status, it continues without scheduling S4 again. Neither status is evidence of novelty.

Example choice submission:

```bash
python scripts/run_preflight.py --profile examples/sample-profile.md --question "Should I build a new ETL framework?" --research-decision quick
python scripts/run_preflight.py --profile examples/sample-profile.md --question "Should I build a new ETL framework?" --research-decision deep
```

The decision flag is accepted only while preflight is awaiting that choice. A quick decision returns `ready` and continues without S4; a deep decision returns `ready` with `run_s4_now: true`.

The skill is designed to work with host-provided search tools, not a proprietary backend.

## 6. Local validation

From the skill root:

```bash
python -m unittest discover -s tests -v
python scripts/run_preflight.py --profile examples/sample-profile.md --question "What should I work on this month?" --mode quick
python scripts/check_recommendation.py --in examples/sample-recommendation.md --retrieval-status NOT_SEARCHED
```

Expected exit codes:

- `0`: ready / valid
- `1`: clarification needed
- `3`: ask quick vs deep before continuing

## 7. Troubleshooting

If the host does not understand the skill:

- confirm that the folder is named `project-navigator`;
- confirm that `SKILL.md` is present at the root;
- confirm the host supports skills and can load a local folder.

If prior-art research is required but the host has no search tool:

- give the user the quick answer with an explicit note that external prior-art research was not performed;
- do not claim novelty without evidence.

## 8. More detail

See [README.md](README.md), [SKILL.md](SKILL.md), and [evaluations/host-agent-test.md](evaluations/host-agent-test.md).
