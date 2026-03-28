"""Loadout: scores and ranks skills against a task description."""

from __future__ import annotations

from agent_maintenance.core.models import Skill
from agent_maintenance.forge.normalizer import SkillNormalizer
from agent_maintenance.providers.base import EmbeddingProvider
from agent_maintenance.providers.embeddings import StubEmbeddingProvider


class SkillRanker:
    """Ranks skills by their relevance to a given task description.

    Uses an EmbeddingProvider for semantic similarity scoring.
    Falls back to the StubEmbeddingProvider if none is supplied.
    """

    def __init__(self, embedding_provider: EmbeddingProvider | None = None) -> None:
        self.provider = embedding_provider or StubEmbeddingProvider()
        self._normalizer = SkillNormalizer()

    def rank(self, task: str, skills: list[Skill]) -> list[tuple[Skill, float]]:
        """Return (skill, score) pairs sorted by descending relevance.

        Args:
            task: A natural-language description of the current task.
            skills: The pool of skills to score.

        Returns:
            List of (Skill, score) tuples, best match first.
        """
        if not skills:
            return []

        task_text = self._normalizer.normalize_text(task)
        skill_texts = [self._normalizer.normalize_skill(s) for s in skills]

        task_embedding = self.provider.embed([task_text])[0]
        skill_embeddings = self.provider.embed(skill_texts)

        scored = [
            (skill, round(self.provider.similarity(task_embedding, emb), 4))
            for skill, emb in zip(skills, skill_embeddings)
        ]
        return sorted(scored, key=lambda pair: pair[1], reverse=True)
