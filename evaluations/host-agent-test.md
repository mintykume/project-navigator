# Host agent integration test plan

This document is a manual integration test for the canonical Project Navigator skill.

## Goal

Confirm that a host agent can load the skill, understand the decision workflow, trigger research only when warranted, and produce a recommendation that complies with the required structure.

## Required host capabilities

The host agent should provide:

- user conversation
- LLM reasoning
- web / GitHub / academic / other search tools when available
- file access if profiles are supplied as local files

Project Navigator remains tool-agnostic. It does not require a proprietary backend.

## Test 1 — Simple project decision

User prompt:

> I want to build an AI tutor. Should I?

Expected behavior:

- ask for clarification if the idea is underspecified;
- inspect the user profile or ask targeted questions;
- decide whether existing-work research is required;
- use host search when needed;
- not immediately say yes;
- output a structured recommendation with evidence, gap, and trade-off.

## Test 2 — Existing or duplicate project

User prompt:

> I want to build a generic todo app with AI summaries and a dashboard.

Expected behavior:

- identify duplicate patterns and low differentiation;
- prefer a stronger problem framing or rejection;
- avoid greenfield build when the idea is low-value and generic.

## Test 3 — Personal-fit mismatch

User prompt:

> I want to build a distributed robotics simulation platform, even though my profile is mainly Python + writing + learning design.

Expected behavior:

- identify that the project may be technically interesting but poorly aligned with the user's current trajectory;
- surface opportunity cost and skill-fit issues;
- prefer a more realistic adjacent project or learning path.

## Test 4 — Genuine opportunity

User prompt:

> I want to build a learning tool for children that explains complexity in a child-friendly way.

Expected behavior:

- find a genuine educational gap if one exists;
- check whether the idea is already productized;
- ask what is actually scarce: curriculum design, child UX, or distribution;
- recommend a narrow first experiment rather than a broad launch.

## Test 5 — Insufficient information

User prompt:

> I want to build something with AI.

Expected behavior:

- ask targeted clarification questions;
- avoid inventing assumptions;
- stop rather than hallucinating a specific recommendation.

## Test 6 — Evidence changes the decision

Run the same project twice:

- A. without prior-art research
- B. with retrieved evidence showing many strong existing solutions

Expected behavior:

- the recommendation becomes more cautious or changes from build to reframe / learn first / drop;
- prior-art evidence should affect the final judgment.

## Pass criteria

A host-agent test passes when the agent:

- loads the skill;
- understands the workflow;
- asks only necessary clarifying questions;
- uses host search when research is required;
- respects the recommendation contract;
- changes its answer when evidence changes;
- avoids always recommending "build".

## Notes

If the host supports only one search backend, use that backend and record the result honestly. Do not claim compatibility with hosts that were not actually tested.
