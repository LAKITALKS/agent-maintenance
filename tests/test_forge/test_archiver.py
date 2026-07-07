"""Tests for the SkillArchiver."""

from pathlib import Path

import pytest

from agent_maintenance.forge.archiver import SkillArchiver


def make_file(directory: Path, name: str, content: str = "skill content") -> Path:
    path = directory / name
    path.write_text(content, encoding="utf-8")
    return path


class TestSkillArchiver:
    def test_archive_moves_file(self, tmp_path: Path) -> None:
        skills = tmp_path / "skills"
        skills.mkdir()
        src = make_file(skills, "skill_a.md", content="content")

        archive_dir = tmp_path / ".archive"
        archiver = SkillArchiver(archive_dir)
        dest = archiver.archive(src)

        assert dest.exists()
        assert not src.exists()
        assert dest.read_text() == "content"

    def test_archive_creates_dated_subdirectory(self, tmp_path: Path) -> None:
        skills = tmp_path / "skills"
        skills.mkdir()
        src = make_file(skills, "skill.md")

        archiver = SkillArchiver(tmp_path / ".archive")
        dest = archiver.archive(src)

        # Parent is a YYYY-MM-DD directory
        import re
        assert re.match(r"\d{4}-\d{2}-\d{2}", dest.parent.name)

    def test_archive_raises_on_missing_file(self, tmp_path: Path) -> None:
        archiver = SkillArchiver(tmp_path / ".archive")
        with pytest.raises(FileNotFoundError, match="Cannot archive missing path"):
            archiver.archive(tmp_path / "nonexistent.md")

    def test_archive_many_moves_all_files(self, tmp_path: Path) -> None:
        skills = tmp_path / "skills"
        skills.mkdir()
        paths = [make_file(skills, f"skill_{i}.md") for i in range(3)]

        archiver = SkillArchiver(tmp_path / ".archive")
        results = archiver.archive_many(paths)

        assert len(results) == 3
        assert all(d.exists() for d in results)
        assert all(not p.exists() for p in paths)

    def test_archive_moves_whole_folder(self, tmp_path: Path) -> None:
        skills = tmp_path / "skills"
        skills.mkdir()
        # A folder skill: SKILL.md plus an extra asset file
        folder = skills / "my_folder_skill"
        (folder / "scripts").mkdir(parents=True)
        (folder / "SKILL.md").write_text("# Folder skill", encoding="utf-8")
        (folder / "reference.md").write_text("reference notes", encoding="utf-8")
        (folder / "scripts" / "check.py").write_text("print('hi')", encoding="utf-8")

        archiver = SkillArchiver(tmp_path / ".archive")
        dest = archiver.archive(folder)

        # The whole folder moved — nothing orphaned in skills/
        assert dest.is_dir()
        assert not folder.exists()
        assert (dest / "SKILL.md").exists()
        assert (dest / "reference.md").read_text() == "reference notes"
        assert (dest / "scripts" / "check.py").exists()

    def test_archive_folder_avoids_overwrite_with_counter(self, tmp_path: Path) -> None:
        skills = tmp_path / "skills"
        skills.mkdir()
        archiver = SkillArchiver(tmp_path / ".archive")

        first = skills / "dup"
        first.mkdir()
        (first / "SKILL.md").write_text("first", encoding="utf-8")
        dest1 = archiver.archive(first)

        second = skills / "dup"
        second.mkdir()
        (second / "SKILL.md").write_text("second", encoding="utf-8")
        dest2 = archiver.archive(second)

        assert dest1 != dest2
        assert (dest1 / "SKILL.md").read_text() == "first"
        assert (dest2 / "SKILL.md").read_text() == "second"

    def test_archive_avoids_overwrite_with_counter(self, tmp_path: Path) -> None:
        skills = tmp_path / "skills"
        skills.mkdir()

        # Two files with the same name from different sources
        src1 = make_file(skills, "skill.md", "first")
        archiver = SkillArchiver(tmp_path / ".archive")
        dest1 = archiver.archive(src1)

        # Restore a file with the same name
        src2 = make_file(skills, "skill.md", "second")
        dest2 = archiver.archive(src2)

        assert dest1 != dest2
        assert dest1.exists()
        assert dest2.exists()
        assert dest1.read_text() == "first"
        assert dest2.read_text() == "second"
