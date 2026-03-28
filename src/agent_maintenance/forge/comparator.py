"""Forge: finds similar or redundant skills (merge candidates)."""

from __future__ import annotations

from agent_maintenance.core.models import MergeCandidate, Skill
from agent_maintenance.forge.normalizer import SkillNormalizer
from agent_maintenance.providers.base import EmbeddingProvider
from agent_maintenance.providers.embeddings import StubEmbeddingProvider


class SkillComparator:
    """Identifies merge candidates by comparing skill similarity.

    Uses an EmbeddingProvider for semantic comparison.
    Falls back to the StubEmbeddingProvider if none is supplied.
    """

    def __init__(
        self,
        embedding_provider: EmbeddingProvider | None = None,
        threshold: float = 0.75,
    ) -> None:
        self.provider = embedding_provider or StubEmbeddingProvider()
        self.threshold = threshold
        self._normalizer = SkillNormalizer()

    def find_merge_candidates(self, skills: list[Skill]) -> list[MergeCandidate]:
        """Return all pairs of skills whose similarity exceeds the threshold."""
        if len(skills) < 2:
            return []

        texts = [self._normalizer.normalize_skill(s) for s in skills]
        embeddings = self.provider.embed(texts)

        candidates: list[MergeCandidate] = []
        for i in range(len(skills)):
            for j in range(i + 1, len(skills)):
                score = self.provider.similarity(embeddings[i], embeddings[j])
                if score >= self.threshold:
                    candidates.append(
                        MergeCandidate(
                            skill_a=skills[i],
                            skill_b=skills[j],
                            similarity_score=round(score, 4),
                            reason="Similarity exceeds threshold",
                        )
                    )

        return sorted(candidates, key=lambda c: c.similarity_score, reverse=True)
