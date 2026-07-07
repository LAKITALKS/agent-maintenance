"""Tests for the shared skill discovery (flat + folder formats)."""

from pathlib import Path

import pytest

from agent_maintenance.core.parser import discover_skills


def write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def make_flat(directory: Path, name: str, body: str = "content") -> Path:
    return write(directory / f"{name}.md", f"# {name}\n\n{body}\n")


def make_folder(directory: Path, name: str, frontmatter: str = "", body: str = "content") -> Path:
    fm = f"---\n{frontmatter}\n---\n\n" if frontmatter else ""
    return write(directory / name / "SKILL.md", f"{fm}# {name}\n\n{body}\n")


class TestDiscoverySelection:
    def test_flat_only(self, tmp_path: Path) -> None:
        make_flat(tmp_path, "alpha")
        make_flat(tmp_path, "beta")
        (tmp_path / "notes.txt").write_text("ignored", encoding="utf-8")

        skills = discover_skills(tmp_path)
        assert sorted(s.name for s in skills) == ["alpha", "beta"]
        assert all(not s.is_folder_skill for s in skills)

    def test_folder_only(self, tmp_path: Path) -> None:
        make_folder(tmp_path, "gamma")
        make_folder(tmp_path, "delta")

        skills = discover_skills(tmp_path)
        assert sorted(s.name for s in skills) == ["delta", "gamma"]
        assert all(s.is_folder_skill for s in skills)

    def test_mixed(self, tmp_path: Path) -> None:
        make_flat(tmp_path, "flat_one")
        make_folder(tmp_path, "folder_one")

        skills = discover_skills(tmp_path)
        by_name = {s.name: s for s in skills}
        assert set(by_name) == {"flat_one", "folder_one"}
        assert by_name["flat_one"].is_folder_skill is False
        assert by_name["folder_one"].is_folder_skill is True

    def test_raises_on_missing_dir(self, tmp_path: Path) -> None:
        with pytest.raises(NotADirectoryError):
            discover_skills(tmp_path / "nonexistent")


class TestDiscoveryIgnores:
    def test_ignores_archive_and_hidden_dirs(self, tmp_path: Path) -> None:
        make_folder(tmp_path, "real")
        # .archive and other hidden folders must be skipped
        write(tmp_path / ".archive" / "old" / "SKILL.md", "# archived")
        write(tmp_path / ".hidden" / "SKILL.md", "# hidden")

        skills = discover_skills(tmp_path)
        assert [s.name for s in skills] == ["real"]

    def test_ignores_nested_too_deep(self, tmp_path: Path) -> None:
        make_folder(tmp_path, "top")
        # SKILL.md nested two levels deep is not a folder skill
        write(tmp_path / "outer" / "inner" / "SKILL.md", "# too deep")

        skills = discover_skills(tmp_path)
        assert [s.name for s in skills] == ["top"]

    def test_ignores_dir_without_skill_md(self, tmp_path: Path) -> None:
        make_folder(tmp_path, "valid")
        (tmp_path / "noise").mkdir()
        (tmp_path / "noise" / "README.md").write_text("not a skill", encoding="utf-8")

        skills = discover_skills(tmp_path)
        assert [s.name for s in skills] == ["valid"]


class TestFolderSkillParsing:
    def test_source_path_is_skill_md_and_archive_target_is_folder(self, tmp_path: Path) -> None:
        make_folder(tmp_path, "designer", frontmatter="name: designer\ndescription: Designs things")

        (skill,) = discover_skills(tmp_path)
        assert skill.is_folder_skill is True
        assert skill.source_path == tmp_path / "designer" / "SKILL.md"
        assert skill.archive_target == tmp_path / "designer"
        assert skill.metadata.description == "Designs things"

    def test_name_falls_back_to_folder_name(self, tmp_path: Path) -> None:
        # No name in frontmatter → folder name, never the literal "SKILL" stem
        make_folder(tmp_path, "my_cool_skill", frontmatter="description: only a description")

        (skill,) = discover_skills(tmp_path)
        assert skill.name == "my_cool_skill"

    def test_minimal_frontmatter_without_tags_is_fine(self, tmp_path: Path) -> None:
        make_folder(tmp_path, "minimal", frontmatter="name: minimal\ndescription: Minimal skill")

        (skill,) = discover_skills(tmp_path)
        assert skill.tags == []  # absence of tags is not an error

    def test_flat_skill_archive_target_is_the_file(self, tmp_path: Path) -> None:
        make_flat(tmp_path, "flat")

        (skill,) = discover_skills(tmp_path)
        assert skill.is_folder_skill is False
        assert skill.archive_target == skill.source_path == tmp_path / "flat.md"
