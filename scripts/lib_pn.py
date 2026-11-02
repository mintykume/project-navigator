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

HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*$", re.MULTILINE)
PROFILE_FIELDS = {
    "name",
    "primary_objective",
    "time_budget",
    "income_urgency",
    "trajectory",
    *CAPABILITY_FIELDS,
    "missing_capabilities",
    "preferences",
    "constraints",
    "artifacts",
    "coding_level",
    "technical_interests",
    "interests",
    "country",
    "city",
}
PREFERENCE_FIELDS = {
    "working_style",
    "research_vs_build",
    "visual_vs_abstract",
    "collaboration",
    "preferred_stack",
    "ethical_boundaries",
}
CONSTRAINT_FIELDS = {"location", "financial", "risk_tolerance", "other"}
PLACEHOLDER_VALUES = frozenset({"-", "tbd", "n/a", "?", "unknown"})


def slug_field(heading: str) -> str:
    heading = re.sub(r"[ \t]+#+[ \t]*$", "", heading.strip())
    heading = re.sub(r"\s*:+\s*$", "", heading)
    return re.sub(r"\s+", "_", heading.strip().lower())


def _is_placeholder(value: Any) -> bool:
    return (
        isinstance(value, str)
        and value.strip().casefold() in PLACEHOLDER_VALUES
    )


def _has_profile_value(value: Any) -> bool:
    if isinstance(value, dict):
        if {"value", "source", "confidence", "freshness"}.issubset(value):
            return _has_profile_value(value.get("value"))
        return any(_has_profile_value(item) for item in value.values())
    if isinstance(value, list):
        return any(_has_profile_value(item) for item in value)
    if isinstance(value, str):
        return bool(value.strip()) and not _is_placeholder(value)
    return value is not None


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
    headings = [
        (match.start(), match.end(), len(match.group(1)), slug_field(match.group(2)))
        for match in HEADING_RE.finditer(text)
    ]
    profile: dict[str, Any] = {}
    for index, (_, heading_end, level, key) in enumerate(headings):
        if key not in PROFILE_FIELDS:
            continue

        body_end = len(text)
        for next_start, _, next_level, next_key in headings[index + 1:]:
            if (
                next_key in PROFILE_FIELDS
                or next_level <= level
                or key not in {"preferences", "constraints"}
            ):
                body_end = next_start
                break
        body = text[heading_end:body_end].strip()
        if key in {"preferences", "constraints"}:
            fields = PREFERENCE_FIELDS if key == "preferences" else CONSTRAINT_FIELDS
            profile[key] = _parse_subsections(body, fields)
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


def _parse_subsections(body: str, fields: set[str]) -> dict[str, Any]:
    headings = [
        (match.start(), match.end(), len(match.group(1)), slug_field(match.group(2)))
        for match in HEADING_RE.finditer(body)
    ]
    out: dict[str, Any] = {}
    for index, (_, heading_end, level, key) in enumerate(headings):
        if key not in fields:
            continue
        chunk_end = len(body)
        if index + 1 < len(headings):
            chunk_end = headings[index + 1][0]
        chunk = body[heading_end:chunk_end].strip()
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
        if not isinstance(val, str) or not _has_profile_value(val):
            errors.append(f"missing_or_empty:{field}")

    caps_ok = False
    for field in CAPABILITY_FIELDS:
        val = profile.get(field)
        if isinstance(val, list) and any(
            isinstance(x, str) and _has_profile_value(x) for x in val
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
        if not isinstance(val, str) or not _has_profile_value(val):
            missing.append(field)

    caps_present = False
    for field in CAPABILITY_FIELDS:
        val = profile.get(field)
        if isinstance(val, list) and any(
            isinstance(x, str) and _has_profile_value(x) for x in val
        ):
            caps_present = True
            break
    if not caps_present:
        # Prefer demonstrated first in the bank order
        missing.append("demonstrated_capabilities")

    # Optional but useful
    optional_checks = [
        ("income_urgency", lambda p: not _has_profile_value(p.get("income_urgency"))),
        ("trajectory", lambda p: not (
            isinstance(p.get("trajectory"), str)
            and _has_profile_value(p["trajectory"])
        )),
        ("artifacts", lambda p: not (
            isinstance(p.get("artifacts"), list)
            and any(
                isinstance(x, str) and _has_profile_value(x)
                for x in p["artifacts"]
            )
        )),
        (
            "constraints.location",
            lambda p: not (
                isinstance(p.get("constraints"), dict)
                and isinstance(p["constraints"].get("location"), str)
                and _has_profile_value(p["constraints"]["location"])
            ),
        ),
        (
            "preferences.research_vs_build",
            lambda p: not (
                isinstance(p.get("preferences"), dict)
                and isinstance(p["preferences"].get("research_vs_build"), str)
                and _has_profile_value(p["preferences"]["research_vs_build"])
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

    def clean(obj: Any, field: str | None = None) -> Any:
        if isinstance(obj, dict):
            out = {k: clean(v, k) for k, v in obj.items()}
            return {k: v for k, v in out.items() if v not in (None, "", [], {})}
        if isinstance(obj, list):
            return [
                item
                for item in (clean(value) for value in obj)
                if item not in (None, "", "-", [])
            ]
        if isinstance(obj, str):
            stripped = obj.strip()
            if _is_placeholder(stripped) and not (
                field == "income_urgency" and stripped.casefold() == "unknown"
            ):
                return None
            return stripped
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


_CODING_LEVEL = re.compile(
    r"\b(beginner|novice|intermediate|advanced|expert)\b",
    re.I,
)
_CODING_CONTEXT = re.compile(
    r"\b(?:coding|programming|software development|coder|programmer|developer)\b",
    re.I,
)
_INTEREST_STATEMENTS = (
    re.compile(
        r"\b(?:interested in|passionate about|focused on)\s+"
        r"([^.!?;,]+)",
        re.I,
    ),
    re.compile(
        r"\b(?:coding\s+)?project ideas?\s+(?:around|about)\s+"
        r"([^.!?;,]+)",
        re.I,
    ),
)
_OBJECTIVE_STATEMENT = re.compile(
    r"\b(?:my\s+(?:main\s+)?(?:goal|objective)\s+is|"
    r"i(?:'m| am)\s+(?:mainly\s+)?optimizing\s+for|"
    r"i\s+want\s+to\s+optimize\s+for)\s+([^.!?;,]+)",
    re.I,
)
_TIME_STATEMENT = re.compile(
    r"\b(?:my\s+time\s+budget\s+is|available\s+time\s+is|"
    r"i\s+have|i['’]ve\s+got|i\s+can\s+(?:spend|commit|dedicate))\s+"
    r"((?:(?:about|around|roughly)\s+)?"
    r"(?:\d+(?:\.\d+)?|one|two|three|four|five|six|seven|eight|nine|ten)\s*"
    r"(?:hours?|hrs?|days?|weeks?|wks?|months?|evenings?|weekends?)"
    r"(?:\s*(?:per|a|/)\s*(?:day|week|month))?|"
    r"(?:this|next)\s+(?:weekend|week|month))",
    re.I,
)


def _normalize_objective(value: str) -> str:
    text = " ".join(value.split()).strip(" ,.;:")
    if re.search(r"\bportfolio\b", text, re.I):
        return "portfolio evidence"
    if re.search(r"\b(?:learn|learning|study)\b", text, re.I):
        return "learning"
    if re.search(r"\b(?:research|literature|paper)\b", text, re.I):
        return "research progress"
    if re.search(r"\b(?:income|money|earn|paid)\b", text, re.I):
        return "income"
    if re.search(r"\b(?:job|career|employability|hired)\b", text, re.I):
        return "employability"
    return text[:160]


def extract_profile_facts_from_question(question: str) -> dict[str, Any]:
    """Extract only explicit, task-relevant profile facts from the current message."""
    text = " ".join((question or "").split())
    if not text:
        return {}

    facts: dict[str, Any] = {}
    level = _CODING_LEVEL.search(text)
    if level and _CODING_CONTEXT.search(text):
        facts["coding_level"] = level.group(1).lower()

    for pattern in _INTEREST_STATEMENTS:
        match = pattern.search(text)
        if match:
            interests = [
                value.strip(" \t\r\n.,;:-")[:120]
                for value in re.split(r"\s*,\s*|\s+(?:and|or)\s+", match.group(1))
                if value.strip(" \t\r\n.,;:-")
            ]
            if interests:
                facts["technical_interests"] = interests[:5]
                break

    objective = _OBJECTIVE_STATEMENT.search(text)
    if objective:
        facts["primary_objective"] = _normalize_objective(objective.group(1))
    elif re.search(r"\b(?:for\s+)?my\s+portfolio\b", text, re.I):
        facts["primary_objective"] = "portfolio evidence"

    time_budget = _TIME_STATEMENT.search(text)
    if time_budget:
        facts["time_budget"] = " ".join(time_budget.group(1).split())
    return facts


def resolve_profile(
    *,
    profile: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
    current_question: str | None = None,
) -> dict[str, Any]:
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

    for field, value in extract_profile_facts_from_question(current_question or "").items():
        set_field(field, value, "current_conversation")

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
        field = field.get("value")
    return field if _has_profile_value(field) else None


def has_local_search_need(question: str) -> bool:
    q = question.lower()
    local_terms = (
        "job", "jobs", "internship", "internships", "scholarship", "scholarships",
        "university", "universities", "company", "companies", "local", "near me",
        "city", "region", "country", "market", "opportunity", "accelerator",
        "event", "hackathon", "meetup", "fellowship", "grant", "coworking",
        "makerspace", "nearby", "in-person", "in person",
    )
    return any(term in q for term in local_terms)


def profile_questions_for_task(question: str, profile: dict[str, Any]) -> list[dict[str, str]]:
    """Return the minimum targeted profile questions that could materially change the recommendation."""
    q = (question or "").lower()
    profile = resolve_profile(profile=profile, current_question=question)["profile"]
    result: list[dict[str, str]] = []
    local_need = has_local_search_need(q)

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

NOT_SEARCHED = "NOT_SEARCHED"
SEARCHED_WITH_RESULTS = "SEARCHED_WITH_RESULTS"
SEARCHED_NO_RESULTS = "SEARCHED_NO_RESULTS"
SEARCHED_NO_USABLE_EVIDENCE = "SEARCHED_NO_USABLE_EVIDENCE"
RETRIEVAL_STATES = {
    NOT_SEARCHED,
    SEARCHED_WITH_RESULTS,
    SEARCHED_NO_RESULTS,
    SEARCHED_NO_USABLE_EVIDENCE,
}


def normalize_retrieval_status(
    retrieval_status: str | None,
    has_retrieval_facts: bool | None = None,
) -> str:
    """Resolve retrieval state; True means validated, relevant evidence exists."""
    if retrieval_status is None:
        return (
            SEARCHED_WITH_RESULTS
            if has_retrieval_facts
            else NOT_SEARCHED
        )
    if (
        not isinstance(retrieval_status, str)
        or retrieval_status not in RETRIEVAL_STATES
    ):
        raise ValueError(
            "retrieval_status must be one of: "
            + ", ".join(sorted(RETRIEVAL_STATES))
        )
    expected_has_facts = retrieval_status == SEARCHED_WITH_RESULTS
    if (
        has_retrieval_facts is not None
        and has_retrieval_facts != expected_has_facts
    ):
        raise ValueError(
            f"retrieval_status {retrieval_status} conflicts with "
            "whether retrieval facts are present"
        )
    return retrieval_status


_BUILD_ACTION = re.compile(
    r"\b(?:build(?:ing|s)?|creat(?:e|es|ed|ing)|mak(?:e|es|ing)|"
    r"ship(?:ping|s|ped)?|launch(?:ing|es|ed)?|"
    r"implement(?:ing|s|ed)?|develop(?:ing|s|ed)?|"
    r"writ(?:e|es|ing|ten)|cod(?:e|es|ing|ed)|"
    r"program(?:ming|s|med)?|prototype(?:d|s|ing)?)\b",
    re.I,
)
_PROJECT_NOUN = re.compile(
    r"\b(?:project|app|application|tool|cli|api|library|framework|"
    r"platform|prototype|mvp|repo|repository|script|automation|bot|"
    r"game|website|service|extension|plugin|product|parser|dashboard|"
    r"portfolio|startup|saas|paper|package)\b",
    re.I,
)
_PROJECT_IDEA = re.compile(
    r"\b(?:project ideas?|ideas? for|idea to|portfolio project|side project|"
    r"i have an? idea|i['’]ve got an? idea)\b",
    re.I,
)
_LEARNING_ONLY = re.compile(
    r"\b(?:what|which)\s+(?:(?:programming|coding)\s+)?"
    r"(?:tool|api|language|framework|technology|skill|course|topic)s?"
    r"\b.{0,45}\b(?:learn|study|practice)\b|"
    r"\b(?:learning path|study plan|what to learn)\b|"
    r"\bhow\s+(?:can|should|do)\s+i\s+(?:learn|study|improve|develop)\s+"
    r"(?:my\s+)?(?:skills|knowledge|expertise)\b|"
    r"\b(?:improve|develop|build)\s+my\s+(?:coding\s+)?skills\b",
    re.I,
)
_EXISTENCE_INTENT = re.compile(
    r"\b(?:already\s+exists?|does\b.{1,80}\bexist|is there\b.{1,80}\b|"
    r"has\b.{1,80}\b(?:been done|already been|ever been)\b|"
    r"has\s+(?:anyone|anybody|someone|somebody)\s+"
    r"(?:ever\s+)?(?:built|made|created|implemented|written|coded|developed)\b|"
    r"prior[- ]art|(?:is|was)\s+this\s+idea\s+(?:original|novel)|"
    r"has this been done before|duplicates?|alternatives?\s+to|"
    r"reinvent(?:ing)?|from scratch|greenfield|anything like this)\b",
    re.I,
)
_NEGATED_BUILD = re.compile(
    r"\b(?:do not|don['’]t|dont|does not|doesn['’]t|should not|shouldn['’]t|"
    r"would not|wouldn['’]t|will not|won['’]t|could not|couldn['’]t|"
    r"never|not)\s+(?:(?:want|plan|intend|need|mean|try|look)\s+)?"
    r"(?:to\s+)?(?:build|create|make|ship|launch|implement|develop|write|"
    r"code|program|prototype)\b|"
    r"\bnot interested in\s+(?:building|creating|making|shipping|launching|"
    r"implementing|developing|writing|coding|programming)\b",
    re.I,
)
_EXPLICIT_BUILD_QUESTION = re.compile(
    r"\b(?:should|could|would|can|shall)\s+i\s+"
    r"(?:maybe\s+|perhaps\s+)?(?:build(?:ing|s)?|create|"
    r"make(?!\s+money)|ship|launch|implement|"
    r"develop|write|code|program|prototype)\b",
    re.I,
)
_BUILD_PROPOSAL = re.compile(
    r"\b(?:i(?:\s+am|['’]m)?|we(?:\s+are|['’]re)?)\s+"
    r"(?:thinking\s+(?:of|about)|considering|planning|want|would like|"
    r"intend|hope)\s+(?:to\s+)?"
    r"(?:build(?:ing|s)?|create|make(?!\s+money)|ship|launch|implement|develop|write|code|"
    r"program|prototype)\b",
    re.I,
)
_WORK_ON_PROJECT = re.compile(
    r"\b(?:work on|pursue|take on|start)\b.{0,60}\b"
    r"(?:project|app|application|tool|cli|api|library|framework|platform|"
    r"prototype|mvp|repo|repository|script|automation|bot|game|website|"
    r"service|extension|plugin|product|parser|dashboard|portfolio)\b",
    re.I,
)
_ACTION_WITH_TARGET = re.compile(
    r"\b(?:build(?:ing|s)?|create|make(?!\s+money)|ship|launch|implement|develop|write|code|"
    r"program|prototype)\s+(?:(?:a|an|the|my|our|this|new|another|small|"
    r"simple|open.source)\s+){0,2}[a-z][\w-]*\b",
    re.I,
)
_IDEA_REQUEST = re.compile(
    r"\b(?:give me|suggest|recommend|brainstorm|looking for|need|want|"
    r"what are)\b.{0,50}\b(?:project ideas?|ideas for a project|"
    r"portfolio projects?|side projects?)\b",
    re.I,
)
_OPTION_COMPARISON = re.compile(
    r"\bwhich\b.{0,50}\b(?:project|idea|app|application|tool|cli|api|"
    r"library|framework|platform|prototype|bot|game|website)\b|"
    r"\bwhich\b.{0,60}\b(?:build|create|make|write|code|develop|work on|"
    r"pursue)\b.{0,40}\b(?:first|between|or|choose|pick)\b|"
    r"\bchoose between\b.{0,80}\b(?:project|idea|app|tool|build)\b",
    re.I,
)
_EXPLICIT_DEEP_REQUEST = re.compile(
    r"\b(?:deep|thorough|comprehensive)\s+(?:prior[- ]art\s+|existing[- ]work\s+)?"
    r"(?:research|search|check|review)\b|"
    r"\b(?:research|search|check|review)\b.{0,35}\b"
    r"(?:deeply|thoroughly|comprehensively|prior[- ]art)\b",
    re.I,
)


def _intent_clauses(question: str) -> list[str]:
    return [
        clause.strip()
        for clause in re.split(r"[.!?;,]+|\bbut\b|\bhowever\b", question)
        if clause.strip()
    ]


def research_signals(question: str) -> dict[str, bool]:
    clauses = _intent_clauses(question.replace("’", "'"))
    existence_intent = bool(_EXISTENCE_INTENT.search(question))
    negated_build_intent = any(_NEGATED_BUILD.search(clause) for clause in clauses)
    build_intent = False
    for clause in clauses:
        if _NEGATED_BUILD.search(clause):
            continue
        is_learning_question = bool(_LEARNING_ONLY.search(clause))
        if is_learning_question and not _PROJECT_IDEA.search(clause):
            continue
        if (
            _EXPLICIT_BUILD_QUESTION.search(clause)
            or _BUILD_PROPOSAL.search(clause)
            or _WORK_ON_PROJECT.search(clause)
            or (_PROJECT_IDEA.search(clause) and (
                _BUILD_ACTION.search(clause)
                or _IDEA_REQUEST.search(clause)
                or re.search(r"\b(?:i have|i['’]ve got)\b", clause, re.I)
            ))
            or _IDEA_REQUEST.search(clause)
            or (
                _BUILD_ACTION.search(clause)
                and _ACTION_WITH_TARGET.search(clause)
                and not re.search(r"\bmake\s+money\b", clause, re.I)
            )
        ):
            build_intent = True
            break

    learning_only = bool(_LEARNING_ONLY.search(question)) and not (
        build_intent or existence_intent or _PROJECT_IDEA.search(question)
    )
    option_comparison = bool(_OPTION_COMPARISON.search(question)) and not learning_only
    return {
        "build_intent": build_intent,
        "existence_intent": existence_intent,
        "option_comparison": option_comparison,
        "learning_only": learning_only,
        "negated_build_intent": negated_build_intent,
        "explicit_deep_request": bool(_EXPLICIT_DEEP_REQUEST.search(question)),
    }


def plan_workflow(
    *,
    question: str,
    profile: dict[str, Any],
    mode: str = "quick",
    research_decision: str | None = None,
    retrieval_status: str | None = None,
    has_retrieval_facts: bool | None = None,
    allow_incomplete: bool = False,
) -> dict[str, Any]:
    """Deterministic stage plan; gates expensive S4 research."""
    if research_decision not in {None, "quick", "deep"}:
        raise ValueError("research_decision must be 'quick' or 'deep'")
    retrieval_status = normalize_retrieval_status(
        retrieval_status,
        has_retrieval_facts,
    )
    has_retrieval_facts = retrieval_status == SEARCHED_WITH_RESULTS
    retrieval_completed = retrieval_status != NOT_SEARCHED

    missing = critical_missing(profile)
    needs_clarification = bool(missing) and not allow_incomplete
    signals = research_signals(question)
    effective_mode = "deep" if signals["explicit_deep_request"] else mode
    urgency = str(profile.get("income_urgency") or "unknown").lower()

    research_justified = False
    reasons: list[str] = []

    if needs_clarification:
        reasons.append("blocked_on_clarification")
    elif retrieval_completed:
        if has_retrieval_facts:
            reasons.append("retrieval_facts_already_present")
        elif retrieval_status == SEARCHED_NO_USABLE_EVIDENCE:
            reasons.append("retrieval_completed_without_usable_evidence")
        else:
            reasons.append("retrieval_completed_without_results")
        research_justified = False
    else:
        if signals["existence_intent"]:
            research_justified = True
            reasons.append("existence_intent")
        if signals["build_intent"]:
            research_justified = True
            reasons.append("build_intent")
        if effective_mode == "deep":
            research_justified = True
            reasons.append(
                "explicit_deep_request"
                if signals["explicit_deep_request"] and mode != "deep"
                else "mode_deep"
            )
        if (
            urgency == "immediate"
            and signals["build_intent"] is False
            and signals["existence_intent"] is False
            and not signals["explicit_deep_request"]
        ):
            research_justified = False
            reasons.append("immediate_urgency_without_build_claim")
        if signals["learning_only"] and not signals["existence_intent"] and not signals["build_intent"]:
            research_justified = False
            reasons.append("learning_only")
        if not reasons:
            reasons.append("no_research_trigger")

    was_awaiting_research_decision = (
        research_justified
        and effective_mode != "deep"
        and not retrieval_completed
        and not needs_clarification
    )
    if research_decision is not None and not was_awaiting_research_decision:
        raise ValueError(
            "research_decision is only valid when the workflow is awaiting a quick/deep choice"
        )
    if research_decision == "deep":
        effective_mode = "deep"

    awaiting_research_decision = (
        was_awaiting_research_decision and research_decision is None
    )
    resolved_research_decision = research_decision
    if resolved_research_decision is None and effective_mode == "deep" and research_justified:
        resolved_research_decision = "deep"

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
        if research_decision == "quick":
            next_action = "continue_without_research"
            skip_s4 = True
        elif research_justified and effective_mode == "deep" and not retrieval_completed:
            active.append("s4_existing_work_check")
            skip_s4 = False
            next_action = "run_existing_work_search"
        elif research_justified and effective_mode != "deep" and not retrieval_completed:
            next_action = "offer_quick_vs_deep"
            skip_s4 = True
        elif retrieval_completed:
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
        "mode": effective_mode,
        "signals": signals,
        "research_justified": research_justified and not needs_clarification,
        "research_decision": resolved_research_decision,
        "awaiting_research_decision": awaiting_research_decision,
        "research_reasons": reasons,
        "run_s4_now": (not skip_s4),
        "skip_s4": skip_s4,
        "has_retrieval_facts": has_retrieval_facts,
        "retrieval_status": retrieval_status,
        "next_action": next_action if not needs_clarification else "ask_clarifying_questions",
        "active_stages": active,
        "stage_files": {s: STAGE_FILES[s] for s in active},
        "load_order": [
            STAGE_FILES[s] for s in active if s != "s9_lint"
        ],
    }
