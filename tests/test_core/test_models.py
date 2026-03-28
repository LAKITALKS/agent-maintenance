"""Tests for core data models."""

import pytest

from agent_maintenance.core.models import MergeCandidate, Skill, SkillMetadata


def make_skill(name: str, tags: list[str] | None = None, description: str = "") -> Skill:
    return Skill(
        metadata=SkillMetadata(name=name, tags=tags or [], description=description),
        content=f"Content for {name}",
    )


class TestSkillMetadata:
    def test_defaults(self) -> None:
        meta = SkillMetadata(name="my_skill")
        assert meta.description == ""
        assert meta.tags == []
        assert meta.version == "1.0"

    def test_name_required(self) -> None:
        with pytest.raises(Exception):
            SkillMetadata()  # type: ignore[call-arg]


class TestSkill:
    def test_name_property(self) -> None:
        skill = make_skill("test_skill")
        assert skill.name == "test_skill"

    def test_tags_property(self) -> None:
        skill = make_skill("s", tags=["python", "debug"])
        assert skill.tags == ["python", "debug"]

    def test_repr(self) -> None:
        skill = make_skill("my_skill", tags=["a"])
        assert "my_skill" in repr(skill)


class TestMergeCandidate:
    def test_valid_score_range(self) -> None:
        a = make_skill("skill_a")
        b = make_skill("skill_b")
        candidate = MergeCandidate(skill_a=a, skill_b=b, similarity_score=0.9)
        assert candidate.similarity_score == 0.9

    def test_score_out_of_range(self) -> None:
        a = make_skill("skill_a")
        b = make_skill("skill_b")
        with pytest.raises(Exception):
            MergeCandidate(skill_a=a, skill_b=b, similarity_score=1.5)
