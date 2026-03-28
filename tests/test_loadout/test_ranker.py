"""Tests for the Loadout SkillRanker and SkillSelector."""

from agent_maintenance.core.models import Skill, SkillMetadata
from agent_maintenance.loadout.ranker import SkillRanker
from agent_maintenance.loadout.selector import SkillSelector


def make_skill(name: str, content: str = "", tags: list[str] | None = None) -> Skill:
    return Skill(
        metadata=SkillMetadata(name=name, tags=tags or []),
        content=content or f"Content for {name}",
    )


class TestSkillRanker:
    def test_returns_all_skills(self) -> None:
        skills = [make_skill(f"skill_{i}") for i in range(4)]
        ranker = SkillRanker()
        ranked = ranker.rank("fix a bug in Python", skills)
        assert len(ranked) == 4

    def test_empty_pool(self) -> None:
        ranker = SkillRanker()
        assert ranker.rank("some task", []) == []

    def test_returns_scores_between_0_and_1(self) -> None:
        skills = [make_skill("s1"), make_skill("s2")]
        ranker = SkillRanker()
        ranked = ranker.rank("task", skills)
        for _skill, score in ranked:
            assert 0.0 <= score <= 1.0


class TestSkillSelector:
    def test_top_k_limits_results(self) -> None:
        skills = [make_skill(f"skill_{i}") for i in range(10)]
        selector = SkillSelector(top_k=3)
        selected = selector.select("some task", skills)
        assert len(selected) == 3

    def test_top_k_larger_than_pool(self) -> None:
        skills = [make_skill(f"skill_{i}") for i in range(2)]
        selector = SkillSelector(top_k=5)
        selected = selector.select("some task", skills)
        assert len(selected) == 2
