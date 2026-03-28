"""Loadout: selects the top-K most relevant skills for a task."""

from __future__ import annotations

from agent_maintenance.core.models import Skill
from agent_maintenance.loadout.ranker import SkillRanker
from agent_maintenance.providers.base import EmbeddingProvider


class SkillSelector:
    """Selects the top-K skills for a given task from a skill pool."""

    def __init__(
        self,
        embedding_provider: EmbeddingProvider | None = None,
        top_k: int = 5,
    ) -> None:
        self.top_k = top_k
        self._ranker = SkillRanker(embedding_provider)

    def select(self, task: str, skills: list[Skill]) -> list[Skill]:
        """Return the top-K skills most relevant to the task.

        Args:
            task: Natural-language task description.
            skills: Full pool of available skills.

        Returns:
            Ordered list of selected skills, best match first.
        """
        ranked = self._ranker.rank(task, skills)
        return [skill for skill, _score in ranked[: self.top_k]]
