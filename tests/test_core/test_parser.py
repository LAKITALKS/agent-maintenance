"""Tests for the skill file parser."""

from pathlib import Path

import pytest

from agent_maintenance.core.parser import parse_skill_file, parse_skills_dir


@pytest.fixture
def skill_with_frontmatter(tmp_path: Path) -> Path:
    content = """\
---
name: my_skill
description: A test skill
tags: [python, testing]
version: "2.0"
---

# My Skill

This is the skill body.
"""
    path = tmp_path / "my_skill.md"
    path.write_text(content, encoding="utf-8")
    return path


@pytest.fixture
def skill_without_frontmatter(tmp_path: Path) -> Path:
    content = "# Bare Skill\n\nJust content, no frontmatter.\n"
    path = tmp_path / "bare_skill.md"
    path.write_text(content, encoding="utf-8")
    return path


class TestParseSkillFile:
    def test_parses_frontmatter(self, skill_with_frontmatter: Path) -> None:
        skill = parse_skill_file(skill_with_frontmatter)
        assert skill.name == "my_skill"
        assert skill.metadata.description == "A test skill"
        assert skill.metadata.tags == ["python", "testing"]
        assert skill.metadata.version == "2.0"

    def test_content_without_frontmatter(self, skill_without_frontmatter: Path) -> None:
        skill = parse_skill_file(skill_without_frontmatter)
        assert skill.name == "bare_skill"  # falls back to filename stem
        assert "Just content" in skill.content

    def test_source_path_set(self, skill_with_frontmatter: Path) -> None:
        skill = parse_skill_file(skill_with_frontmatter)
        assert skill.source_path == skill_with_frontmatter


class TestParseSkillsDir:
    def test_parses_all_md_files(self, tmp_path: Path) -> None:
        for name in ("alpha.md", "beta.md", "gamma.md"):
            (tmp_path / name).write_text(f"# {name}\n\nContent.", encoding="utf-8")
        (tmp_path / "not_a_skill.txt").write_text("ignored", encoding="utf-8")

        skills = parse_skills_dir(tmp_path)
        assert len(skills) == 3

    def test_raises_on_missing_dir(self, tmp_path: Path) -> None:
        with pytest.raises(NotADirectoryError):
            parse_skills_dir(tmp_path / "nonexistent")
