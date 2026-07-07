"""Parser for skill Markdown files with optional YAML frontmatter."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from agent_maintenance.core.models import Skill, SkillMetadata

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


SKILL_MD_FILENAME = "SKILL.md"


def parse_skill_file(
    path: Path,
    *,
    is_folder_skill: bool = False,
    name_fallback: str | None = None,
) -> Skill:
    """Parse a single skill Markdown file into a Skill object.

    Handles files with or without YAML frontmatter.
    The skill name is taken from frontmatter ``name`` when present, otherwise it
    falls back to ``name_fallback`` (the folder name for folder skills) and
    finally to the filename stem.

    For folder-format skills (``skills/<name>/SKILL.md``) pass
    ``is_folder_skill=True`` and ``name_fallback=<folder name>`` so that the
    resulting Skill archives as a whole folder and does not derive its name from
    the literal stem ``"SKILL"``.
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

    # Derive name: frontmatter wins, then the folder-name fallback, then stem.
    name = str(frontmatter.get("name") or name_fallback or path.stem)

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
        is_folder_skill=is_folder_skill,
    )


def discover_skills(directory: Path) -> list[Skill]:
    """Discover and parse every skill in a directory, both layouts supported.

    This is the single source of truth for skill discovery. It finds:

    - Legacy flat skills: ``directory/*.md``
    - Standard folder skills: ``directory/<skill-name>/SKILL.md``

    Deliberately skipped:

    - Hidden folders (names starting with ``.``), which also excludes
      ``.archive/``.
    - Sub-folders without a top-level ``SKILL.md`` (noise directories).
    - ``SKILL.md`` files nested deeper than one level — only the immediate
      children of ``directory`` are treated as folder skills.

    Results are returned with flat skills first (sorted by path) followed by
    folder skills (sorted by folder name), preserving legacy ordering for
    flat-only libraries.
    """
    if not directory.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")

    skills: list[Skill] = []

    # Legacy flat skills: directory/*.md
    for path in sorted(directory.glob("*.md")):
        if path.is_file():
            skills.append(parse_skill_file(path))

    # Standard folder skills: directory/<skill-name>/SKILL.md
    for child in sorted(directory.iterdir()):
        if not child.is_dir() or child.name.startswith("."):
            continue
        skill_md = child / SKILL_MD_FILENAME
        if skill_md.is_file():
            skills.append(
                parse_skill_file(skill_md, is_folder_skill=True, name_fallback=child.name)
            )

    return skills


def parse_skills_dir(directory: Path) -> list[Skill]:
    """Parse all skills in a directory into Skill objects.

    Thin backwards-compatible alias for :func:`discover_skills`; both flat and
    folder-format skills are returned.
    """
    return discover_skills(directory)
