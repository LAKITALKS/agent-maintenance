"""Forge: serializes Skill objects back to Markdown files with YAML frontmatter."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from agent_maintenance.core.models import Skill


def write_skill_file(skill: Skill, path: Path) -> None:
    """Write a Skill to a Markdown file.

    Uses skill.raw_frontmatter when populated (preferred — preserves all metadata
    including custom fields like source_skills and merged_by).
    Falls back to a minimal dict derived from skill.metadata.

    The output format:
        ---
        <yaml frontmatter>
        ---

        <markdown content>
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    frontmatter = skill.raw_frontmatter if skill.raw_frontmatter else _metadata_to_dict(skill)
    yaml_text = yaml.dump(
        frontmatter,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )
    path.write_text(f"---\n{yaml_text}---\n\n{skill.content}\n", encoding="utf-8")


def _metadata_to_dict(skill: Skill) -> dict[str, Any]:
    d: dict[str, Any] = {
        "name": skill.metadata.name,
        "description": skill.metadata.description,
        "tags": skill.metadata.tags,
        "version": skill.metadata.version,
    }
    return {k: v for k, v in d.items() if v or v == 0}
