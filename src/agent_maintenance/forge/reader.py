"""Forge: reads skill files from a directory."""

from __future__ import annotations

from pathlib import Path

from agent_maintenance.core.models import Skill
from agent_maintenance.core.parser import discover_skills, parse_skill_file


class SkillReader:
    """Loads skill files from a directory into Skill objects.

    Discovery is delegated to :func:`discover_skills`, so both legacy flat
    ``*.md`` skills and folder-format ``<skill-name>/SKILL.md`` skills are
    supported through a single shared code path.
    """

    def __init__(self, skills_dir: Path) -> None:
        self.skills_dir = skills_dir

    def read_all(self) -> list[Skill]:
        """Return all skills found in the configured directory."""
        return discover_skills(self.skills_dir)

    def read_one(self, path: Path) -> Skill:
        """Parse a single skill file."""
        return parse_skill_file(path)

    def list_paths(self) -> list[Path]:
        """Return the parsed Markdown path of every discovered skill.

        For folder skills this is the ``SKILL.md`` inside the folder.
        """
        return [s.source_path for s in discover_skills(self.skills_dir) if s.source_path]
