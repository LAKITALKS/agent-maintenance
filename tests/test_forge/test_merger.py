"""Tests for the SkillMerger and skill file writer."""

from pathlib import Path

import pytest

from agent_maintenance.core.models import Skill, SkillMetadata
from agent_maintenance.forge.merger import SkillMerger
from agent_maintenance.forge.writer import write_skill_file
from agent_maintenance.providers.llm import StubLLMProvider


def make_skill(name: str, content: str = "", tags: list[str] | None = None) -> Skill:
    return Skill(
        metadata=SkillMetadata(name=name, tags=tags or [], description=f"About {name}"),
        content=content or f"# {name}\n\nSome content.",
    )


class TestSkillMerger:
    def setup_method(self) -> None:
        self.merger = SkillMerger(llm_provider=StubLLMProvider())

    def test_merge_returns_skill(self) -> None:
        skills = [make_skill("a"), make_skill("b")]
        result = self.merger.merge(skills)
        assert isinstance(result, Skill)

    def test_merged_name_two_skills_no_common_tag(self) -> None:
        # No shared tags → fallback: {a}_{b}_merged
        skills = [make_skill("alpha"), make_skill("beta")]
        result = self.merger.merge(skills)
        assert result.name == "alpha_beta_merged"

    def test_merged_name_uses_longest_common_tag(self) -> None:
        # Shared tags: "react" (5), "useeffect" (9) → picks "useeffect"
        skills = [
            make_skill("a", tags=["react", "useeffect"]),
            make_skill("b", tags=["react", "useeffect", "hooks"]),
        ]
        result = self.merger.merge(skills)
        assert result.name == "useeffect_merged"

    def test_merged_name_three_skills_no_common_tag(self) -> None:
        # No shared tags, 3+ skills → {first}_merged
        skills = [make_skill("x"), make_skill("y"), make_skill("z")]
        result = self.merger.merge(skills)
        assert result.name == "x_merged"

    def test_tags_are_unioned(self) -> None:
        skills = [make_skill("a", tags=["python", "debug"]), make_skill("b", tags=["debug", "api"])]
        result = self.merger.merge(skills)
        assert set(result.tags) == {"python", "debug", "api"}

    def test_source_skills_in_frontmatter(self) -> None:
        skills = [make_skill("x"), make_skill("y")]
        result = self.merger.merge(skills)
        assert result.raw_frontmatter["source_skills"] == ["x", "y"]
        assert result.raw_frontmatter["merged_by"] == "agent-maintenance"

    def test_stub_produces_structural_merge(self) -> None:
        skills = [make_skill("a"), make_skill("b")]
        result = self.merger.merge(skills)
        # Stub → structural merge fallback
        assert result.raw_frontmatter["merge_method"] == "structural"
        assert "Structural merge" in result.content

    def test_structural_merge_contains_source_content(self) -> None:
        skills = [
            make_skill("a", content="Unique content from skill A"),
            make_skill("b", content="Unique content from skill B"),
        ]
        result = self.merger.merge(skills)
        assert "Unique content from skill A" in result.content
        assert "Unique content from skill B" in result.content

    def test_requires_at_least_two_skills(self) -> None:
        with pytest.raises(ValueError, match="at least 2"):
            self.merger.merge([make_skill("alone")])

    def test_description_references_sources(self) -> None:
        skills = [make_skill("foo"), make_skill("bar")]
        result = self.merger.merge(skills)
        assert "foo" in result.metadata.description
        assert "bar" in result.metadata.description


class TestWriteSkillFile:
    def test_writes_file_with_frontmatter(self, tmp_path: Path) -> None:
        skill = make_skill("my_skill")
        dest = tmp_path / "my_skill.md"
        write_skill_file(skill, dest)
        assert dest.exists()
        text = dest.read_text(encoding="utf-8")
        assert text.startswith("---\n")
        assert "my_skill" in text

    def test_written_file_is_parseable(self, tmp_path: Path) -> None:
        from agent_maintenance.core.parser import parse_skill_file

        skill = make_skill("roundtrip", content="## Core steps\n\n1. Do the thing.")
        dest = tmp_path / "roundtrip.md"
        write_skill_file(skill, dest)
        parsed = parse_skill_file(dest)
        assert parsed.name == "roundtrip"
        assert "Do the thing" in parsed.content

    def test_raw_frontmatter_preserved(self, tmp_path: Path) -> None:
        skill = Skill(
            metadata=SkillMetadata(name="merged"),
            content="content",
            raw_frontmatter={
                "name": "merged",
                "source_skills": ["a", "b"],
                "merged_by": "agent-maintenance",
            },
        )
        dest = tmp_path / "merged.md"
        write_skill_file(skill, dest)
        text = dest.read_text()
        assert "source_skills" in text
        assert "agent-maintenance" in text

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        skill = make_skill("deep")
        dest = tmp_path / "a" / "b" / "deep.md"
        write_skill_file(skill, dest)
        assert dest.exists()
