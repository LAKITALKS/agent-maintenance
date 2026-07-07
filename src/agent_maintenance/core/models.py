"""Core data models shared across Forge and Loadout."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SkillMetadata(BaseModel):
    """Structured metadata parsed from a skill file's YAML frontmatter."""

    model_config = ConfigDict(extra="allow")  # preserve unknown frontmatter keys

    name: str
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    version: str = "1.0"
    created: datetime | None = None
    updated: datetime | None = None


class Skill(BaseModel):
    """A single skill loaded from a Markdown file.

    Two on-disk layouts are supported:

    - Legacy flat skill: a standalone ``skills/<name>.md`` file.
    - Folder skill: a ``skills/<name>/SKILL.md`` file, optionally accompanied
      by scripts, references, or other assets in the same folder.

    In both cases ``source_path`` points at the Markdown file that was parsed.
    ``is_folder_skill`` and ``archive_target`` capture the difference so that
    archiving moves the whole folder for folder skills, never just SKILL.md.
    """

    metadata: SkillMetadata
    content: str
    source_path: Path | None = None
    raw_frontmatter: dict[str, Any] = Field(default_factory=dict)
    is_folder_skill: bool = False

    @property
    def name(self) -> str:
        return self.metadata.name

    @property
    def tags(self) -> list[str]:
        return self.metadata.tags

    @property
    def archive_target(self) -> Path | None:
        """The filesystem entry to archive for this skill.

        - Legacy flat skill → the Markdown file itself (``source_path``).
        - Folder skill → the enclosing folder (``source_path.parent``), so that
          scripts, references, and assets travel with the SKILL.md.

        Returns ``None`` when the skill has no ``source_path`` (e.g. synthesised
        meta-skills that have not been written to disk yet).
        """
        if self.source_path is None:
            return None
        return self.source_path.parent if self.is_folder_skill else self.source_path

    def __repr__(self) -> str:
        return f"Skill(name={self.name!r}, tags={self.tags})"


class MergeCandidate(BaseModel):
    """A pair of skills identified as potentially redundant or overlapping."""

    skill_a: Skill
    skill_b: Skill
    similarity_score: float = Field(ge=0.0, le=1.0)
    reason: str = ""

    def __repr__(self) -> str:
        return (
            f"MergeCandidate({self.skill_a.name!r} ↔ {self.skill_b.name!r}, "
            f"score={self.similarity_score:.2f})"
        )


class LoadoutResult(BaseModel):
    """The output of a Loadout prepare run."""

    task_description: str
    selected_skills: list[Skill]
    output_path: Path | None = None

    @property
    def skill_names(self) -> list[str]:
        return [s.name for s in self.selected_skills]
