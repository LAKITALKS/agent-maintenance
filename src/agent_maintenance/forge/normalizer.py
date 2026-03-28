"""Forge: normalises skill content for consistent comparison."""

from __future__ import annotations

import re

from agent_maintenance.core.models import Skill


class SkillNormalizer:
    """Produces a normalised text representation of a skill for comparison.

    Normalisation removes noise (extra whitespace, punctuation variants)
    so that textual similarity checks are more reliable.
    """

    def normalize_text(self, text: str) -> str:
        """Return a lowercase, whitespace-collapsed version of the text."""
        text = text.lower()
        text = re.sub(r"[^\w\s]", " ", text)  # strip punctuation
        text = re.sub(r"\s+", " ", text)       # collapse whitespace
        return text.strip()

    def normalize_skill(self, skill: Skill) -> str:
        """Return a single normalised string representing the full skill.

        Combines name, description, tags, and content for a holistic view.
        """
        parts = [
            skill.metadata.name,
            skill.metadata.description,
            " ".join(skill.metadata.tags),
            skill.content,
        ]
        combined = " ".join(p for p in parts if p)
        return self.normalize_text(combined)

    def enrich_metadata(self, skill: Skill) -> Skill:
        """Fill in missing metadata fields where they can be inferred.

        Currently infers a description from the first non-empty content line
        if no description is present.
        """
        if skill.metadata.description:
            return skill

        first_line = next(
            (
                line.strip().lstrip("#").strip()
                for line in skill.content.splitlines()
                if line.strip()
            ),
            "",
        )
        updated_meta = skill.metadata.model_copy(update={"description": first_line})
        return skill.model_copy(update={"metadata": updated_meta})
