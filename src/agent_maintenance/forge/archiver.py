"""Forge: safely archives skill files instead of deleting them."""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path


class SkillArchiver:
    """Moves skill files into a timestamped archive directory.

    Files are never deleted — they are moved to preserve history.
    Archive layout:  <archive_dir>/<YYYY-MM-DD>/<original_filename>
    """

    def __init__(self, archive_dir: Path) -> None:
        self.archive_dir = archive_dir

    def archive(self, path: Path) -> Path:
        """Move a skill file to the archive and return the new path."""
        if not path.exists():
            raise FileNotFoundError(f"Cannot archive missing file: {path}")

        dated_dir = self.archive_dir / datetime.now().strftime("%Y-%m-%d")
        dated_dir.mkdir(parents=True, exist_ok=True)

        dest = self._unique_dest(dated_dir, path.name)
        shutil.move(str(path), str(dest))
        return dest

    def archive_many(self, paths: list[Path]) -> list[Path]:
        """Archive multiple files and return their new paths."""
        return [self.archive(p) for p in paths]

    def _unique_dest(self, directory: Path, filename: str) -> Path:
        """Avoid overwriting an existing archive entry by appending a counter."""
        dest = directory / filename
        if not dest.exists():
            return dest

        stem = Path(filename).stem
        suffix = Path(filename).suffix
        counter = 1
        while dest.exists():
            dest = directory / f"{stem}_{counter}{suffix}"
            counter += 1
        return dest
