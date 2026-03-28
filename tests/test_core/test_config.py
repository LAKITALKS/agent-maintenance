"""Tests for config loading."""

from pathlib import Path

import pytest

from agent_maintenance.core.config import AppConfig, load_config


class TestAppConfig:
    def test_defaults(self) -> None:
        config = AppConfig()
        assert config.skills_dir == Path("skills")
        assert config.top_k == 5
        assert config.similarity_threshold == 0.75
        assert config.embedding_model is None

    def test_apply_overrides_non_none(self) -> None:
        config = AppConfig()
        updated = config.apply_overrides(top_k=10, skills_dir=Path("custom"))
        assert updated.top_k == 10
        assert updated.skills_dir == Path("custom")

    def test_apply_overrides_ignores_none(self) -> None:
        config = AppConfig(top_k=7)
        updated = config.apply_overrides(top_k=None, skills_dir=None)
        assert updated.top_k == 7  # unchanged

    def test_apply_overrides_returns_same_if_all_none(self) -> None:
        config = AppConfig(top_k=3)
        updated = config.apply_overrides(top_k=None)
        assert updated.top_k == 3


class TestLoadConfig:
    def test_returns_defaults_when_no_file(self, tmp_path: Path) -> None:
        config = load_config(tmp_path / "missing.toml")
        assert config == AppConfig()

    def test_loads_valid_toml(self, tmp_path: Path) -> None:
        toml_file = tmp_path / "agent-maintenance.toml"
        toml_file.write_text(
            '[tool.agent-maintenance]\n'
            'top_k = 3\n'
            'similarity_threshold = 0.85\n'
            'skills_dir = "my-skills"\n',
            encoding="utf-8",
        )
        # Pydantic accepts extra keys, load only root-level keys
        simple_toml = tmp_path / "simple.toml"
        simple_toml.write_text(
            'top_k = 3\n'
            'similarity_threshold = 0.85\n',
            encoding="utf-8",
        )
        config = load_config(simple_toml)
        assert config.top_k == 3
        assert config.similarity_threshold == 0.85

    def test_raises_on_invalid_toml(self, tmp_path: Path) -> None:
        bad_file = tmp_path / "bad.toml"
        bad_file.write_text("this is not [ valid toml }{", encoding="utf-8")
        with pytest.raises(ValueError, match="Invalid TOML"):
            load_config(bad_file)

    def test_embedding_model_configurable(self, tmp_path: Path) -> None:
        toml_file = tmp_path / "cfg.toml"
        toml_file.write_text('embedding_model = "paraphrase-MiniLM-L3-v2"\n', encoding="utf-8")
        config = load_config(toml_file)
        assert config.embedding_model == "paraphrase-MiniLM-L3-v2"
