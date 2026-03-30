"""Forge: generates a consolidated meta-skill from a cluster of related skills."""

from __future__ import annotations

import re
from datetime import datetime

from agent_maintenance.core.models import Skill, SkillMetadata
from agent_maintenance.providers.base import LLMProvider

# Marker emitted by StubLLMProvider — used to detect when no real LLM is active
_STUB_MARKER = "[StubLLMProvider]"

_SYSTEM_PROMPT = """\
You are a technical writing assistant for developer skill documentation.
Consolidate the provided skill files into one concise meta-skill.

Rules:
- Preserve all unique, actionable information; remove all redundancy
- The result must be shorter and more useful than reading all originals
- Use exactly this Markdown structure (omit empty sections):

## When to apply
[one short paragraph]

## Core steps
[numbered list — concrete and actionable]

## Warnings / Anti-patterns
[bullet list]

## Notes
[brief extra context, only if genuinely useful]

Write only the body — no YAML frontmatter, no top-level heading.
"""

# ── Section parsing ────────────────────────────────────────────────────────────

_SECTION_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)

# Canonical section aliases (normalised to lowercase for lookup)
_WHEN_KEYS: frozenset[str] = frozenset({"when to apply", "when to use", "when", "use when"})
_STEPS_KEYS: frozenset[str] = frozenset({"core steps", "steps", "usage", "how to use", "how to"})
_WARNINGS_KEYS: frozenset[str] = frozenset(
    {"warnings", "anti-patterns", "warnings / anti-patterns", "pitfalls", "caveats"}
)
_NOTES_KEYS: frozenset[str] = frozenset({"notes", "note", "additional notes", "remarks"})
_ALL_KNOWN: frozenset[str] = _WHEN_KEYS | _STEPS_KEYS | _WARNINGS_KEYS | _NOTES_KEYS


def _parse_sections(content: str) -> dict[str, str]:
    """Split Markdown content into ``{heading: body}`` pairs at the ``##`` level."""
    matches = list(_SECTION_RE.finditer(content))
    result: dict[str, str] = {}
    for i, match in enumerate(matches):
        title = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        body = content[start:end].strip()
        result[title] = body
    return result


def _dedup_bullets(blocks: list[str]) -> str:
    """Merge bullet-point blocks, discarding exact duplicate lines.

    Preserves the first occurrence of every non-empty line across all blocks.
    """
    seen: dict[str, None] = {}
    for block in blocks:
        for line in block.splitlines():
            stripped = line.strip()
            if stripped:
                seen.setdefault(stripped, None)
    return "\n".join(seen)


def _structural_merge(skills: list[Skill]) -> str:
    """Template-based merge with section synthesis.

    Organises content by section type across all source skills, deduplicates
    bullet-point warnings, and produces a clean structured output without naive
    full-content concatenation.

    Skills whose content contains no ``##`` headings have their full body
    appended verbatim under a source attribution header.
    """
    parsed: list[tuple[Skill, dict[str, str]]] = [
        (skill, _parse_sections(skill.content)) for skill in skills
    ]

    def collect(keys: frozenset[str]) -> list[tuple[str, str]]:
        """Collect (skill_name, body) for the first matching section heading."""
        result: list[tuple[str, str]] = []
        for skill, sections in parsed:
            for heading, body in sections.items():
                if heading.lower() in keys and body:
                    result.append((skill.name, body))
                    break
        return result

    parts: list[str] = [
        "> **Structural merge** — no LLM provider was active during this run.\n"
        "> For a compressed summary, configure an LLM: set `ANTHROPIC_API_KEY` "
        "or start Ollama locally (`ollama serve`)."
    ]

    # ── When to apply ──────────────────────────────────────────────────────
    when_items = collect(_WHEN_KEYS)
    if when_items:
        parts.append("## When to apply")
        for name, body in when_items:
            parts.append(f"**From `{name}`:** {body}")

    # ── Core steps ─────────────────────────────────────────────────────────
    steps_items = collect(_STEPS_KEYS)
    if steps_items:
        parts.append("## Core steps")
        for name, body in steps_items:
            parts.append(f"*From `{name}`:*\n\n{body}")

    # ── Warnings / Anti-patterns (deduplicated across all sources) ─────────
    warnings_items = collect(_WARNINGS_KEYS)
    if warnings_items:
        parts.append("## Warnings / Anti-patterns")
        deduped = _dedup_bullets([body for _, body in warnings_items])
        parts.append(deduped)

    # ── Notes ──────────────────────────────────────────────────────────────
    notes_items = collect(_NOTES_KEYS)
    if notes_items:
        parts.append("## Notes")
        for name, body in notes_items:
            parts.append(f"*From `{name}`:*\n\n{body}")

    # ── Non-standard sections — preserved with source attribution ──────────
    for skill, sections in parsed:
        for heading, body in sections.items():
            if heading.lower() not in _ALL_KNOWN and body:
                parts.append(f"## {heading} *(from `{skill.name}`)*\n\n{body}")

    # ── Skills with no parseable sections — full content verbatim ──────────
    for skill, sections in parsed:
        if not sections and skill.content.strip():
            parts.append(f"## From: `{skill.name}`\n\n{skill.content}")

    return "\n\n".join(parts)


# ── Naming helpers ────────────────────────────────────────────────────────────

def _user_prompt(skills: list[Skill]) -> str:
    sections = [
        f"### {skill.name}\n\n{skill.content}"
        for skill in skills
    ]
    return (
        f"Consolidate these {len(skills)} skills into one meta-skill:\n\n"
        + "\n\n---\n\n".join(sections)
    )


def _common_tags(skills: list[Skill]) -> set[str]:
    """Return the set of tags shared by every skill in the cluster."""
    if not skills:
        return set()
    shared = set(skills[0].tags)
    for s in skills[1:]:
        shared &= set(s.tags)
    return shared


def _merged_name(skills: list[Skill]) -> str:
    """Derive a human-readable filename for the merged skill.

    Priority:
    1. Most specific (longest) shared tag across all skills → ``{tag}_merged``
    2. Two skills with no common tag                        → ``{a}_{b}_merged``
    3. Three or more skills with no common tag              → ``{first}_merged``
    """
    common = _common_tags(skills)
    if common:
        label = max(common, key=len)
        return f"{label}_merged"
    if len(skills) == 2:
        return f"{skills[0].name}_{skills[1].name}_merged"
    return f"{skills[0].name}_merged"


def _merged_tags(skills: list[Skill]) -> list[str]:
    """Deduplicated union of all source skill tags, preserving insertion order."""
    seen: dict[str, None] = {}
    for skill in skills:
        for tag in skill.tags:
            seen.setdefault(tag, None)
    return list(seen)


def _merged_description(skills: list[Skill]) -> str:
    """Synthesise a description from source skill descriptions.

    When sources have their own descriptions, the first unique phrases are
    combined (capped at 120 characters) before the source attribution.
    Falls back to a plain attribution when no descriptions are available.
    """
    source_names = ", ".join(s.name for s in skills)
    descs = [s.metadata.description for s in skills if s.metadata.description.strip()]
    if descs:
        combined = "; ".join(descs)
        if len(combined) <= 120:
            return f"{combined} — consolidated from: {source_names}"
    return f"Consolidated from: {source_names}"


# ── Merger ────────────────────────────────────────────────────────────────────

class SkillMerger:
    """Generates a consolidated meta-skill from a cluster of related skills.

    Uses an LLMProvider to produce a compressed, structured summary.
    Detects the StubLLMProvider response and falls back to a structural merge,
    so the tool never silently produces LLM-flavoured placeholder text.
    """

    def __init__(self, llm_provider: LLMProvider) -> None:
        self._llm = llm_provider

    def merge(self, skills: list[Skill]) -> Skill:
        """Produce a single consolidated Skill from a group of related skills."""
        if len(skills) < 2:
            raise ValueError(f"merge() requires at least 2 skills, got {len(skills)}")

        llm_output = self._llm.complete(_user_prompt(skills), system=_SYSTEM_PROMPT)

        if _STUB_MARKER in llm_output:
            content = _structural_merge(skills)
            merge_method = "structural"
        else:
            content = llm_output.strip()
            merge_method = "llm"

        source_names = [s.name for s in skills]
        name = _merged_name(skills)
        description = _merged_description(skills)

        metadata = SkillMetadata(
            name=name,
            description=description,
            tags=_merged_tags(skills),
            updated=datetime.now(),
        )

        raw_frontmatter: dict = {
            "name": name,
            "description": description,
            "tags": metadata.tags,
            "version": "1.0",
            "source_skills": source_names,
            "merged_by": "agent-maintenance",
            "merge_method": merge_method,
        }

        return Skill(
            metadata=metadata,
            content=content,
            raw_frontmatter=raw_frontmatter,
        )
