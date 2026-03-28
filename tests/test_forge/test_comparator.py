"""Tests for the SkillComparator."""

from unittest.mock import MagicMock

from agent_maintenance.core.models import Skill, SkillMetadata
from agent_maintenance.forge.comparator import SkillComparator
from agent_maintenance.providers.base import EmbeddingProvider


def make_skill(name: str, content: str = "", tags: list[str] | None = None) -> Skill:
    return Skill(
        metadata=SkillMetadata(name=name, tags=tags or []),
        content=content or f"Content of {name}",
    )


def _fixed_provider(scores: dict[tuple[int, int], float]) -> EmbeddingProvider:
    """Provider that returns unit vectors and maps index-pairs to preset similarity scores."""
    provider = MagicMock(spec=EmbeddingProvider)
    n = max(max(i, j) for i, j in scores) + 1
    # Each skill gets a unique unit vector (identity-like, padded with zeros)
    vectors = [[1.0 if k == i else 0.0 for k in range(n)] for i in range(n)]
    provider.embed.return_value = vectors

    def sim(a: list[float], b: list[float]) -> float:
        idx_a = next(i for i, v in enumerate(vectors) if v == a)
        idx_b = next(i for i, v in enumerate(vectors) if v == b)
        key = (min(idx_a, idx_b), max(idx_a, idx_b))
        return scores.get(key, 0.0)

    provider.similarity.side_effect = sim
    return provider


class TestSkillComparator:
    def test_returns_empty_for_single_skill(self) -> None:
        comparator = SkillComparator()
        assert comparator.find_merge_candidates([make_skill("a")]) == []

    def test_returns_empty_for_empty_list(self) -> None:
        comparator = SkillComparator()
        assert comparator.find_merge_candidates([]) == []

    def test_finds_candidate_above_threshold(self) -> None:
        provider = _fixed_provider({(0, 1): 0.90})
        skills = [make_skill("a"), make_skill("b")]
        comparator = SkillComparator(embedding_provider=provider, threshold=0.80)
        candidates = comparator.find_merge_candidates(skills)
        assert len(candidates) == 1
        assert {candidates[0].skill_a.name, candidates[0].skill_b.name} == {"a", "b"}

    def test_excludes_candidate_below_threshold(self) -> None:
        provider = _fixed_provider({(0, 1): 0.60})
        skills = [make_skill("a"), make_skill("b")]
        comparator = SkillComparator(embedding_provider=provider, threshold=0.75)
        assert comparator.find_merge_candidates(skills) == []

    def test_results_sorted_by_score_descending(self) -> None:
        provider = _fixed_provider({(0, 1): 0.95, (0, 2): 0.80, (1, 2): 0.85})
        skills = [make_skill("a"), make_skill("b"), make_skill("c")]
        comparator = SkillComparator(embedding_provider=provider, threshold=0.75)
        candidates = comparator.find_merge_candidates(skills)
        scores = [c.similarity_score for c in candidates]
        assert scores == sorted(scores, reverse=True)

    def test_score_is_rounded(self) -> None:
        provider = _fixed_provider({(0, 1): 0.876543})
        skills = [make_skill("a"), make_skill("b")]
        comparator = SkillComparator(embedding_provider=provider, threshold=0.75)
        candidates = comparator.find_merge_candidates(skills)
        assert candidates[0].similarity_score == round(0.876543, 4)

    def test_uses_stub_provider_by_default(self) -> None:
        # Should not raise — stub provider is wired in by default
        skills = [make_skill("x"), make_skill("y")]
        comparator = SkillComparator()
        result = comparator.find_merge_candidates(skills)
        assert isinstance(result, list)
