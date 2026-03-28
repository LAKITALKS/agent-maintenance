"""Forge: generates a consolidated meta-skill from a cluster of related skills."""

from __future__ import annotations

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


def _user_prompt(skills: list[Skill]) -> str:
    sections = [
        f"### {skill.name}\n\n{skill.content}"
        for skill in skills
    ]
    return (
        f"Consolidate these {len(skills)} skills into one meta-skill:\n\n"
        + "\n\n---\n\n".join(sections)
    )


def _structural_merge(skills: list[Skill]) -> str:
    """Template-based merge used when no real LLM provider is active.

    Produces readable output, but not compressed.
    A note in the output signals that an LLM pass would improve the result.
    """
    header = (
        "> **Structural merge** — no LLM provider was active during this run.\n"
        "> Re-run with a configured LLM provider for a proper compressed summary.\n"
    )
    parts = [header]
    for skill in skills:
        parts.append(f"## From: `{skill.name}`\n\n{skill.content}")
    return "\n\n---\n\n".join(parts)


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
    2. Two skills with no common tag               → ``{a}_{b}_merged``
    3. Three or more skills with no common tag     → ``{first}_merged``
    """
    common = _common_tags(skills)
    if common:
        label = max(common, key=len)
        return f"{label}_merged"
    if len(skills) == 2:
        return f"{skills[0].name}_{skills[1].name}_merged"
    return f"{skills[0].name}_merged"


def _merged_tags(skills: list[Skill]) -> list[str]:
    """Deduplicated union of all source skill tags, preserving order."""
    seen: dict[str, None] = {}
    for skill in skills:
        for tag in skill.tags:
            seen.setdefault(tag, None)
    return list(seen)


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

        metadata = SkillMetadata(
            name=name,
            description=f"Consolidated from: {', '.join(source_names)}",
            tags=_merged_tags(skills),
            updated=datetime.now(),
        )

        raw_frontmatter: dict = {
            "name": name,
            "description": metadata.description,
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
