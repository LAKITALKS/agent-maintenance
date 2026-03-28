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
    """A single skill loaded from a Markdown file."""

    metadata: SkillMetadata
    content: str
    source_path: Path | None = None
    raw_frontmatter: dict[str, Any] = Field(default_factory=dict)

    @property
    def name(self) -> str:
        return self.metadata.name

    @property
    def tags(self) -> list[str]:
        return self.metadata.tags

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
