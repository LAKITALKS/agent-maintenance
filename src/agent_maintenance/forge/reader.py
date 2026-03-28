"""Forge: reads skill files from a directory."""

from __future__ import annotations

from pathlib import Path

from agent_maintenance.core.models import Skill
from agent_maintenance.core.parser import parse_skill_file, parse_skills_dir


class SkillReader:
    """Loads skill files from a directory into Skill objects."""

    def __init__(self, skills_dir: Path) -> None:
        self.skills_dir = skills_dir

    def read_all(self) -> list[Skill]:
        """Return all skills found in the configured directory."""
        return parse_skills_dir(self.skills_dir)

    def read_one(self, path: Path) -> Skill:
        """Parse a single skill file."""
        return parse_skill_file(path)

    def list_paths(self) -> list[Path]:
        """Return paths to all Markdown files in the skills directory."""
        if not self.skills_dir.is_dir():
            raise NotADirectoryError(f"Not a directory: {self.skills_dir}")
        return sorted(self.skills_dir.glob("*.md"))
