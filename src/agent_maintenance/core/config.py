"""Application configuration with optional TOML file support."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from pydantic import BaseModel

CONFIG_FILENAME = "agent-maintenance.toml"


class AppConfig(BaseModel):
    """Runtime configuration for agent-maintenance.

    Can be loaded from agent-maintenance.toml in the working directory.
    CLI flags always override file-based values.
    """

    skills_dir: Path = Path("skills")
    archive_dir: Path = Path(".archive")
    output_dir: Path = Path("loadout")
    top_k: int = 5
    similarity_threshold: float = 0.75
    embedding_model: str | None = None  # None → use provider default
    llm_model: str | None = None        # None → use provider default (claude-haiku-4-5-20251001)

    def resolve(self) -> AppConfig:
        """Return a copy with all paths resolved to absolute."""
        return self.model_copy(
            update={
                "skills_dir": self.skills_dir.resolve(),
                "archive_dir": self.archive_dir.resolve(),
                "output_dir": self.output_dir.resolve(),
            }
        )

    def apply_overrides(self, **overrides: Any) -> AppConfig:
        """Return a copy with only the non-None overrides applied.

        Intended for merging CLI flags on top of file-based config:
            config = load_config().apply_overrides(skills_dir=cli_flag, top_k=cli_k)
        """
        updates = {k: v for k, v in overrides.items() if v is not None}
        return self.model_copy(update=updates) if updates else self


def load_config(path: Path | None = None) -> AppConfig:
    """Load AppConfig from a TOML file.

    Looks for agent-maintenance.toml in the current directory by default.
    Returns default AppConfig silently if no file is found.
    Raises ValueError if the file exists but contains invalid TOML.

    Args:
        path: Explicit path to a config file. Overrides the default lookup.
    """
    config_path = path or Path(CONFIG_FILENAME)

    if not config_path.exists():
        return AppConfig()

    try:
        with open(config_path, "rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"Invalid TOML in {config_path}: {exc}") from exc

    return AppConfig(**data)
