"""CLI-level tests for `forge run`: the stub safety guard and folder archiving."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from agent_maintenance.cli import forge as forge_cli
from agent_maintenance.providers.embeddings import StubEmbeddingProvider
from agent_maintenance.providers.llm import StubLLMProvider

runner = CliRunner()


@pytest.fixture(autouse=True)
def force_stub_providers(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pin both providers to their stubs so behaviour is deterministic in CI."""
    monkeypatch.setattr(
        forge_cli, "get_embedding_provider", lambda *a, **k: StubEmbeddingProvider()
    )
    monkeypatch.setattr(forge_cli, "get_llm_provider", lambda *a, **k: StubLLMProvider())


def make_flat(directory: Path, name: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{name}.md"
    path.write_text(f"# {name}\n\nSome shared content about {name}.\n", encoding="utf-8")
    return path


def make_folder(directory: Path, name: str) -> Path:
    folder = directory / name
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {name} skill\n---\n\n# {name}\n\nShared content.\n",
        encoding="utf-8",
    )
    (folder / "reference.md").write_text(f"reference for {name}", encoding="utf-8")
    return folder


class TestStubGuard:
    def test_non_dry_run_with_stub_aborts_and_moves_nothing(self, tmp_path: Path) -> None:
        skills = tmp_path / "skills"
        a = make_flat(skills, "one")
        b = make_flat(skills, "two")

        result = runner.invoke(
            forge_cli.app,
            ["run", "--skills-dir", str(skills), "--archive-dir", str(tmp_path / ".archive")],
        )

        assert result.exit_code != 0
        assert "stub embeddings" in result.stdout.lower()
        assert "--allow-unsafe-stub-merge" in result.stdout
        # Nothing was archived or removed
        assert a.exists() and b.exists()
        assert not (tmp_path / ".archive").exists()

    def test_dry_run_with_stub_is_allowed(self, tmp_path: Path) -> None:
        skills = tmp_path / "skills"
        make_flat(skills, "one")
        make_flat(skills, "two")

        result = runner.invoke(
            forge_cli.app,
            ["run", "--skills-dir", str(skills), "--dry-run"],
        )

        assert result.exit_code == 0

    def test_allow_unsafe_flag_permits_run(self, tmp_path: Path) -> None:
        skills = tmp_path / "skills"
        make_flat(skills, "one")
        make_flat(skills, "two")

        result = runner.invoke(
            forge_cli.app,
            [
                "run",
                "--skills-dir",
                str(skills),
                "--archive-dir",
                str(tmp_path / ".archive"),
                "--threshold",
                "0.0",  # force every pair to cluster with meaningless stub scores
                "--allow-unsafe-stub-merge",
            ],
        )

        assert result.exit_code == 0


class TestFolderArchiving:
    def test_folder_skill_archived_as_whole_folder(self, tmp_path: Path) -> None:
        skills = tmp_path / "skills"
        f1 = make_folder(skills, "folder_a")
        f2 = make_folder(skills, "folder_b")
        archive = tmp_path / ".archive"

        result = runner.invoke(
            forge_cli.app,
            [
                "run",
                "--skills-dir",
                str(skills),
                "--archive-dir",
                str(archive),
                "--threshold",
                "0.0",
                "--allow-unsafe-stub-merge",
            ],
        )

        assert result.exit_code == 0
        # Original folders were moved out entirely — no orphans left behind
        assert not f1.exists()
        assert not f2.exists()

        # The whole folder, including the extra asset, landed in the archive
        archived_refs = list(archive.rglob("reference.md"))
        archived_skill_mds = list(archive.rglob("SKILL.md"))
        assert len(archived_refs) == 2
        assert len(archived_skill_mds) == 2

        # A merged meta-skill was written back into the skills directory
        assert any(p.name != "folder_a" and p.suffix == ".md" for p in skills.glob("*.md"))
