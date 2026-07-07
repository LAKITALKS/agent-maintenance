"""Tests for the LoadoutWriter directory-copy mode (flat + folder skills)."""

from pathlib import Path

from agent_maintenance.core.models import LoadoutResult, Skill, SkillMetadata
from agent_maintenance.loadout.writer import LoadoutWriter


def make_flat_skill(directory: Path, name: str) -> Skill:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{name}.md"
    path.write_text(f"# {name}\n\ncontent\n", encoding="utf-8")
    return Skill(
        metadata=SkillMetadata(name=name),
        content="content",
        source_path=path,
        is_folder_skill=False,
    )


def make_folder_skill(directory: Path, name: str) -> Skill:
    folder = directory / name
    (folder / "scripts").mkdir(parents=True, exist_ok=True)
    skill_md = folder / "SKILL.md"
    skill_md.write_text(f"# {name}\n\ncontent\n", encoding="utf-8")
    (folder / "reference.md").write_text(f"ref {name}", encoding="utf-8")
    (folder / "scripts" / "run.py").write_text("print('x')", encoding="utf-8")
    return Skill(
        metadata=SkillMetadata(name=name),
        content="content",
        source_path=skill_md,
        is_folder_skill=True,
    )


class TestWriteLoadoutDir:
    def test_two_folder_skills_stay_separate(self, tmp_path: Path) -> None:
        src = tmp_path / "skills"
        skills = [make_folder_skill(src, "alpha"), make_folder_skill(src, "beta")]
        result = LoadoutResult(task_description="t", selected_skills=skills)

        out = tmp_path / "loadout"
        LoadoutWriter().write_loadout_dir(result, out)

        # Two distinct folders, not one overwritten SKILL.md
        assert (out / "alpha" / "SKILL.md").exists()
        assert (out / "beta" / "SKILL.md").exists()
        assert not (out / "SKILL.md").exists()

    def test_folder_skill_includes_extra_files(self, tmp_path: Path) -> None:
        src = tmp_path / "skills"
        skills = [make_folder_skill(src, "alpha")]
        result = LoadoutResult(task_description="t", selected_skills=skills)

        out = tmp_path / "loadout"
        LoadoutWriter().write_loadout_dir(result, out)

        assert (out / "alpha" / "reference.md").read_text() == "ref alpha"
        assert (out / "alpha" / "scripts" / "run.py").exists()

    def test_flat_skill_copy_still_works(self, tmp_path: Path) -> None:
        src = tmp_path / "skills"
        skills = [make_flat_skill(src, "flat")]
        result = LoadoutResult(task_description="t", selected_skills=skills)

        out = tmp_path / "loadout"
        LoadoutWriter().write_loadout_dir(result, out)

        assert (out / "flat.md").exists()
        assert (out / "flat.md").read_text() == "# flat\n\ncontent\n"

    def test_mixed_flat_and_folder(self, tmp_path: Path) -> None:
        src = tmp_path / "skills"
        skills = [make_flat_skill(src, "flat"), make_folder_skill(src, "folder")]
        result = LoadoutResult(task_description="t", selected_skills=skills)

        out = tmp_path / "loadout"
        LoadoutWriter().write_loadout_dir(result, out)

        assert (out / "flat.md").exists()
        assert (out / "folder" / "SKILL.md").exists()
