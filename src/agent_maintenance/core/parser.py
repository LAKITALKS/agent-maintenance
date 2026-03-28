"""Parser for skill Markdown files with optional YAML frontmatter."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from agent_maintenance.core.models import Skill, SkillMetadata

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_skill_file(path: Path) -> Skill:
    """Parse a single skill Markdown file into a Skill object.

    Handles files with or without YAML frontmatter.
    The skill name falls back to the filename stem if not set in frontmatter.
    """
    raw = path.read_text(encoding="utf-8")
    frontmatter: dict[str, Any] = {}
    content = raw

    match = _FRONTMATTER_RE.match(raw)
    if match:
        try:
            frontmatter = yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError as exc:
            raise ValueError(f"Invalid YAML frontmatter in {path}: {exc}") from exc
        content = raw[match.end():]

    # Derive name from frontmatter or fall back to filename stem
    name = str(frontmatter.get("name", path.stem))

    metadata = SkillMetadata(
        name=name,
        description=str(frontmatter.get("description", "")),
        tags=list(frontmatter.get("tags", [])),
        version=str(frontmatter.get("version", "1.0")),
        created=frontmatter.get("created"),
        updated=frontmatter.get("updated"),
    )

    return Skill(
        metadata=metadata,
        content=content.strip(),
        source_path=path,
        raw_frontmatter=frontmatter,
    )


def parse_skills_dir(directory: Path) -> list[Skill]:
    """Parse all Markdown files in a directory into Skill objects."""
    if not directory.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")

    skills = []
    for path in sorted(directory.glob("*.md")):
        skills.append(parse_skill_file(path))
    return skills
