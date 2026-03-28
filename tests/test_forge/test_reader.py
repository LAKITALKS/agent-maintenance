"""Tests for the Forge SkillReader."""

from pathlib import Path

import pytest

from agent_maintenance.forge.reader import SkillReader


@pytest.fixture
def skills_dir(tmp_path: Path) -> Path:
    for name in ("skill_a.md", "skill_b.md"):
        (tmp_path / name).write_text(f"# {name}\n\nContent.", encoding="utf-8")
    return tmp_path


class TestSkillReader:
    def test_read_all(self, skills_dir: Path) -> None:
        reader = SkillReader(skills_dir)
        skills = reader.read_all()
        assert len(skills) == 2

    def test_list_paths(self, skills_dir: Path) -> None:
        reader = SkillReader(skills_dir)
        paths = reader.list_paths()
        assert all(p.suffix == ".md" for p in paths)
        assert len(paths) == 2

    def test_missing_dir_raises(self, tmp_path: Path) -> None:
        reader = SkillReader(tmp_path / "missing")
        with pytest.raises(NotADirectoryError):
            reader.read_all()
