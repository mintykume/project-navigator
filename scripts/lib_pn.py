"""Shared helpers for Project Navigator scripts (stdlib only)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
PROMPTS = ROOT / "prompts"
TEMPLATES = ROOT / "templates"

CRITICAL_FIELDS = ("primary_objective", "time_budget")
CAPABILITY_FIELDS = (
    "demonstrated_capabilities",
    "claimed_capabilities",
    "emerging_capabilities",
)

HEADING_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
SUBHEADING_RE = re.compile(r"^###\s+(.+?)\s*$", re.MULTILINE)


def slug_field(heading: str) -> str:
    return heading.strip().lower().replace(" ", "_")


def parse_list_block(text: str) -> list[str]:
    items: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s in {"-", "*", "<!--", "-->"}:
            continue
        if s.startswith("<!--"):
            continue
        if s.startswith(("-", "*")):
            s = s.lstrip("-*").strip()
        if s and not s.startswith("<!--"):
            items.append(s)
    return items


def parse_profile_markdown(text: str) -> dict[str, Any]:
    """Parse templates/user-profile.md style markdown into a dict."""
    text = text.replace("\r\n", "\n")
    parts = HEADING_RE.split(text)
    # parts: [preamble, h1, body1, h2, body2, ...]
    profile: dict[str, Any] = {}
    if len(parts) < 3:
        return profile

    for i in range(1, len(parts), 2):
        key = slug_field(parts[i])
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        if key in {"preferences", "constraints"}:
            profile[key] = _parse_subsections(body)
        elif key in CAPABILITY_FIELDS or key in {
            "missing_capabilities",
            "artifacts",
        }:
            profile[key] = parse_list_block(body)
        elif key == "income_urgency":
            val = _first_non_comment_line(body).lower()
            profile[key] = val if val else "unknown"
        else:
            profile[key] = _first_paragraph(body)

    return profile


def _parse_subsections(body: str) -> dict[str, Any]:
    parts = SUBHEADING_RE.split(body)
    out: dict[str, Any] = {}
    if len(parts) < 3:
        return out
    for i in range(1, len(parts), 2):
        key = slug_field(parts[i])
        chunk = parts[i + 1].strip() if i + 1 < len(parts) else ""
        if key == "preferred_stack":
            out[key] = parse_list_block(chunk)
        else:
            out[key] = _first_paragraph(chunk)
    return out


def _first_non_comment_line(body: str) -> str:
    for line in body.splitlines():
        s = line.strip()
        if not s or s.startswith("<!--"):
            continue
        return s
    return ""


def _first_paragraph(body: str) -> str:
    lines: list[str] = []
    for line in body.splitlines():
        s = line.strip()
        if s.startswith("<!--"):
            continue
        if not s:
            if lines:
                break
            continue
        lines.append(s)
    return " ".join(lines).strip()


def load_profile(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("profile JSON must be an object")
        return data
    return parse_profile_markdown(raw)


def validate_profile(profile: dict[str, Any]) -> list[str]:
    """Return list of error strings; empty means structurally OK for critical rules."""
    errors: list[str] = []
    for field in CRITICAL_FIELDS:
        val = profile.get(field)
        if not isinstance(val, str) or not val.strip():
            errors.append(f"missing_or_empty:{field}")

    caps_ok = False
    for field in CAPABILITY_FIELDS:
        val = profile.get(field)
        if isinstance(val, list) and any(
            isinstance(x, str) and x.strip() and x.strip() != "-" for x in val
        ):
            caps_ok = True
            break
    if not caps_ok:
        errors.append("missing_or_empty:capabilities")

    urgency = profile.get("income_urgency", "unknown")
    if urgency not in {None, "none", "soon", "immediate", "unknown"}:
        errors.append("invalid:income_urgency")

    return errors


def missing_field_ids(profile: dict[str, Any]) -> list[str]:
    """Ordered missing field ids for clarification bank."""
    missing: list[str] = []
    for field in CRITICAL_FIELDS:
        val = profile.get(field)
        if not isinstance(val, str) or not val.strip():
            missing.append(field)

    caps_present = False
    for field in CAPABILITY_FIELDS:
        val = profile.get(field)
        if isinstance(val, list) and any(
            isinstance(x, str) and x.strip() and x.strip() != "-" for x in val
        ):
            caps_present = True
            break
    if not caps_present:
        # Prefer demonstrated first in the bank order
        missing.append("demonstrated_capabilities")

    # Optional but useful
    optional_checks = [
        ("income_urgency", lambda p: p.get("income_urgency") in (None, "", "unknown")),
        ("trajectory", lambda p: not (isinstance(p.get("trajectory"), str) and p["trajectory"].strip())),
        ("artifacts", lambda p: not (
            isinstance(p.get("artifacts"), list)
            and any(isinstance(x, str) and x.strip() and x != "-" for x in p["artifacts"])
        )),
        (
            "constraints.location",
            lambda p: not (
                isinstance(p.get("constraints"), dict)
                and isinstance(p["constraints"].get("location"), str)
                and p["constraints"]["location"].strip()
            ),
        ),
        (
            "preferences.research_vs_build",
            lambda p: not (
                isinstance(p.get("preferences"), dict)
                and isinstance(p["preferences"].get("research_vs_build"), str)
                and p["preferences"]["research_vs_build"].strip()
            ),
        ),
    ]
    for field_id, pred in optional_checks:
        if pred(profile) and field_id not in missing:
            missing.append(field_id)

    return missing


def critical_missing(profile: dict[str, Any]) -> list[str]:
    return [
        f
        for f in missing_field_ids(profile)
        if f in CRITICAL_FIELDS or f == "demonstrated_capabilities"
    ]


def compact_profile(profile: dict[str, Any]) -> dict[str, Any]:
    """Drop empties to keep context packs small."""

    def clean(obj: Any) -> Any:
        if isinstance(obj, dict):
            out = {k: clean(v) for k, v in obj.items()}
            return {k: v for k, v in out.items() if v not in (None, "", [], {})}
        if isinstance(obj, list):
            return [x for x in (clean(i) for i in obj) if x not in (None, "", "-", [])]
        if isinstance(obj, str):
            return obj.strip()
        return obj

    return clean(profile)


def _field_mode(source_name: str, explicit: bool) -> tuple[str, float, str]:
    """Return source label, confidence, and freshness for a resolved field."""
    source_map = {
        "current_conversation": "conversation_context",
        "conversation_history": "conversation_context",
        "memory": "persistent_memory",
        "host_context": "host_context",
        "profile": "known_profile",
    }
    source = source_map.get(source_name, source_name)
    confidence = 1.0 if explicit else 0.6
    if explicit and source in {"known_profile", "conversation_context"}:
        confidence = 0.9 if source == "known_profile" else 0.96
    freshness = "recent" if source in {"conversation_context", "host_context"} else "historical"
    if not explicit:
        freshness = "recent" if source in {"host_context", "conversation_context"} else "inferred"
    return source, confidence, freshness


def resolve_profile(*, profile: dict[str, Any] | None = None, context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Blend host, memory, and current-conversation profile data without fabricating facts.

    Returns a normalized dict with both a legacy-compatible plain profile and metadata per field.
    """
    merged: dict[str, Any] = {}
    metadata: dict[str, Any] = {}
    contradictions: list[str] = []
    sources: dict[str, Any] = {}

    def seen_value(key: str) -> Any:
        return merged.get(key)

    def set_field(field: str, value: Any, source_name: str, explicit: bool = True) -> None:
        if field is None or field == "":
            return
        source, confidence, freshness = _field_mode(source_name, explicit)
        item = {"value": value, "source": source, "confidence": round(confidence, 2), "freshness": freshness}
        if not explicit:
            item["inference"] = True
        if field in metadata:
            prior = metadata[field]
            prior_value = prior.get("value")
            if prior_value != value:
                if explicit and prior.get("source") and prior.get("source") != source:
                    contradictions.append(f"{field}: {prior_value!r} -> {value!r} ({source})")
            if not explicit and prior.get("confidence", 0.0) >= item["confidence"]:
                return
            if explicit and prior.get("source") and source in {"known_profile", "conversation_context", "host_context"}:
                if prior.get("confidence", 0.0) > item["confidence"] and prior.get("value") != value:
                    return
        metadata[field] = item
        merged[field] = value
        sources[field] = source

    base_sources = [
        ("profile", profile or {}),
        ("host_context", (context or {}).get("host_context", {})),
        ("memory", (context or {}).get("memory", {})),
        ("conversation_history", (context or {}).get("conversation_history", {})),
        ("current_conversation", (context or {}).get("current_conversation", {})),
    ]

    for source_name, source_data in base_sources:
        if not isinstance(source_data, dict):
            continue
        for field, value in source_data.items():
            if field in {"profile_metadata", "profile", "sources", "contradictions"}:
                continue
            if isinstance(value, dict) and {"value", "source", "confidence", "freshness"}.issubset(value.keys()):
                set_field(field, value.get("value"), source_name, explicit=not value.get("inference", False))
            else:
                set_field(field, value, source_name, explicit=True)

    if isinstance(context, dict):
        for field, value in (context.get("inferred_profile", {}) or {}).items():
            set_field(field, value, "host_context", explicit=False)

    plain_profile = {k: v for k, v in merged.items() if not isinstance(v, (dict, list)) or v}
    if isinstance(profile, dict):
        for key, value in profile.items():
            if key not in plain_profile and key not in {"profile_metadata", "sources", "contradictions"}:
                plain_profile[key] = value
    return {
        "profile": plain_profile,
        "profile_metadata": metadata,
        "contradictions": contradictions,
        "sources": sources,
    }


def _profile_field_value(profile: dict[str, Any], key: str) -> Any:
    field = profile.get(key)
    if isinstance(field, dict) and "value" in field:
        return field.get("value")
    return field


def _has_local_search_need(question: str) -> bool:
    q = question.lower()
    local_terms = (
        "job", "jobs", "internship", "internships", "scholarship", "scholarships",
        "university", "universities", "company", "companies", "local", "near me",
        "city", "region", "country", "market", "opportunity", "accelerator", "event",
    )
    return any(term in q for term in local_terms)


def profile_questions_for_task(question: str, profile: dict[str, Any]) -> list[dict[str, str]]:
    """Return the minimum targeted profile questions that could materially change the recommendation."""
    q = (question or "").lower()
    result: list[dict[str, str]] = []
    local_need = _has_local_search_need(q)

    def ask(field: str, text: str) -> None:
        if not any(item.get("field") == field for item in result):
            result.append({"field": field, "text": text})

    # Practical decision-critical questions.
    if not _profile_field_value(profile, "coding_level"):
        ask("coding_level", "Before I compare these properly: how would you rate your coding level — beginner, comfortable with basics, intermediate, or advanced?")
    if not _profile_field_value(profile, "technical_interests") and not _profile_field_value(profile, "interests"):
        ask("interests", "Which areas are you most interested in right now? Pick as many as you want: AI/ML, backend, frontend, data, cybersecurity, hardware/IoT, education, sustainability, creative tech, business/product, or something else.")
    if not _profile_field_value(profile, "primary_objective"):
        ask("primary_objective", "What are you mainly optimizing for right now: learning, portfolio evidence, employability, income, research, or something else?")
    if local_need and not _profile_field_value(profile, "country"):
        ask("country", "Which country should I use for local opportunities? If you want city-level recommendations, you can also give me your city.")
    if local_need and _profile_field_value(profile, "country") and any(term in q for term in ("city", "region", "near me", "my area", "local area")) and not _profile_field_value(profile, "city"):
        ask("city", "If city-level relevance matters for this recommendation, which city or region should I prioritize?")

    # Do not ask for large profile surveys for generic ranking tasks.
    if "which of these" in q or "compare" in q or "rank" in q:
        # Only ask for the fields that genuinely affect the ranking.
        for field in ("coding_level", "technical_interests"):
            if not _profile_field_value(profile, field):
                ask(field, result[-1]["text"] if result else "I can compare these, but one detail matters a lot for ranking: what is your coding level?")
        return result

    # For coarse project decisions, allow unrelated missing profile fields to pass without blocking.
    return result


def profile_summary(profile: dict[str, Any]) -> dict[str, Any]:
    """Return a compact summary of the resolved profile for request assembly."""
    resolved = resolve_profile(profile=profile)
    summary = {
        "profile": resolved["profile"],
        "metadata": resolved["profile_metadata"],
        "contradictions": resolved["contradictions"],
    }
    return summary


def read_question_bank() -> dict[str, str]:
    path = TEMPLATES / "clarifying-questions.md"
    text = path.read_text(encoding="utf-8")
    bank: dict[str, str] = {}
    for line in text.splitlines():
        if not line.startswith("|") or line.startswith("| field_id"):
            continue
        if re.match(r"^\|\s*-+", line):
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) >= 2:
            field_id = cols[0].strip("`").strip()
            question = cols[1].strip()
            if field_id and question:
                bank[field_id] = question
    return bank


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def configure_stdio() -> None:
    """Best-effort UTF-8 stdout/stderr for Windows consoles."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except Exception:
            pass


def write_text(path: Path | None, text: str) -> None:
    """Write UTF-8 to a file, or print to stdout with safe encoding."""
    if path is not None:
        path.write_text(text, encoding="utf-8")
        return
    configure_stdio()
    try:
        sys.stdout.write(text)
    except UnicodeEncodeError:
        sys.stdout.buffer.write(text.encode("utf-8", errors="replace"))
        if not text.endswith("\n"):
            sys.stdout.buffer.write(b"\n")


def strip_html_comments(text: str) -> str:
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# --- Workflow planning (deterministic gates) ---

STAGE_ORDER = [
    "profile_resolution",
    "s1_clarify",
    "s2_constraints_objective",
    "s3_existing_work_gate",
    "s4_existing_work_check",
    "s5_gaps",
    "s6_trajectory_leverage",
    "s7_horizon_tradeoff",
    "s8_recommend",
    "s9_lint",
]

STAGE_FILES = {
    "profile_resolution": "prompts/stages/profile-resolution.md",
    "s1_clarify": "prompts/stages/s1-clarify.md",
    "s2_constraints_objective": "prompts/stages/s2-constraints-objective.md",
    "s3_existing_work_gate": "prompts/stages/s3-existing-work-gate.md",
    "s4_existing_work_check": "prompts/stages/s4-existing-work-check.md",
    "s5_gaps": "prompts/stages/s5-gaps.md",
    "s6_trajectory_leverage": "prompts/stages/s6-trajectory-leverage.md",
    "s7_horizon_tradeoff": "prompts/stages/s7-horizon-tradeoff.md",
    "s8_recommend": "prompts/stages/s8-recommend.md",
    "s9_lint": "scripts/check_recommendation.py",
}

_BUILD_INTENT = re.compile(
    r"\b("
    r"build|create|make|ship|launch|implement|develop|hackathon|"
    r"dashboard|app|application|saas|startup|tool|cli|api|library|"
    r"framework|platform|prototype|mvp|repo|repository"
    r")\b",
    re.I,
)
_EXISTENCE_INTENT = re.compile(
    r"\b("
    r"already exist|does .+ exist|is there (an?|any)|prior art|"
    r"duplicate|alternatives? to|reinvent|novel|from scratch|greenfield"
    r")\b",
    re.I,
)
_PRIORITIZE_ONLY = re.compile(
    r"\b(which (should|of)|prioritiz|rank these|between .+ and .+|"
    r"learn(ing)? path|study plan|what to learn)\b",
    re.I,
)


def research_signals(question: str) -> dict[str, bool]:
    q = question.strip()
    return {
        "build_intent": bool(_BUILD_INTENT.search(q)),
        "existence_intent": bool(_EXISTENCE_INTENT.search(q)),
        "prioritize_only": bool(_PRIORITIZE_ONLY.search(q)),
    }


def plan_workflow(
    *,
    question: str,
    profile: dict[str, Any],
    mode: str = "quick",
    has_retrieval_facts: bool = False,
    allow_incomplete: bool = False,
) -> dict[str, Any]:
    """Deterministic stage plan; gates expensive S4 research."""
    missing = critical_missing(profile)
    needs_clarification = bool(missing) and not allow_incomplete
    signals = research_signals(question)
    urgency = str(profile.get("income_urgency") or "unknown").lower()

    research_justified = False
    reasons: list[str] = []

    if needs_clarification:
        reasons.append("blocked_on_clarification")
    elif has_retrieval_facts:
        reasons.append("retrieval_facts_already_present")
        research_justified = False
    else:
        if signals["existence_intent"]:
            research_justified = True
            reasons.append("existence_intent")
        if signals["build_intent"] and not signals["prioritize_only"]:
            research_justified = True
            reasons.append("build_intent")
        if mode == "deep":
            research_justified = True
            reasons.append("mode_deep")
        if (
            urgency == "immediate"
            and signals["build_intent"] is False
            and signals["existence_intent"] is False
        ):
            research_justified = False
            reasons.append("immediate_urgency_without_build_claim")
        if signals["prioritize_only"] and not signals["existence_intent"] and not signals["build_intent"]:
            research_justified = False
            reasons.append("prioritize_only")
        if not reasons:
            reasons.append("no_research_trigger")

    # Active stages
    if needs_clarification:
        active = ["profile_resolution", "s1_clarify"]
        next_action = "ask_clarifying_questions"
        skip_s4 = True
    else:
        active = [
            "profile_resolution",
            "s1_clarify",
            "s2_constraints_objective",
            "s3_existing_work_gate",
        ]
        skip_s4 = True
        if research_justified and mode == "deep" and not has_retrieval_facts:
            active.append("s4_existing_work_check")
            skip_s4 = False
            next_action = "run_existing_work_search"
        elif research_justified and mode != "deep" and not has_retrieval_facts:
            next_action = "offer_quick_vs_deep"
            skip_s4 = True
        elif has_retrieval_facts:
            next_action = "continue_from_gaps"
            skip_s4 = True
        else:
            next_action = "continue_without_research"
            skip_s4 = True

        active.extend(
            [
                "s5_gaps",
                "s6_trajectory_leverage",
                "s7_horizon_tradeoff",
                "s8_recommend",
                "s9_lint",
            ]
        )

    return {
        "version": 1,
        "needs_clarification": needs_clarification,
        "critical_missing": missing,
        "mode": mode,
        "signals": signals,
        "research_justified": research_justified and not needs_clarification,
        "research_reasons": reasons,
        "run_s4_now": (not skip_s4),
        "skip_s4": skip_s4,
        "has_retrieval_facts": has_retrieval_facts,
        "next_action": next_action if not needs_clarification else "ask_clarifying_questions",
        "active_stages": active,
        "stage_files": {s: STAGE_FILES[s] for s in active},
        "load_order": [
            STAGE_FILES[s] for s in active if s != "s9_lint"
        ],
    }

