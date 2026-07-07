# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-07-07

### Added
- **Folder-format skills**: alongside legacy flat `skills/*.md` files, the
  standard Agent Skills layout `skills/<skill-name>/SKILL.md` is now discovered
  and parsed. `name` falls back to the folder name when absent from frontmatter.
- Single shared discovery function `discover_skills()` in `core.parser` — all
  skill reading and listing now routes through it, removing duplicated glob logic.
- `Skill.is_folder_skill` flag and `Skill.archive_target` property, so archiving
  can act on the whole folder (folder skills) or the single file (flat skills).
- Stub-embedding safety guard: a destructive `forge run` is now **refused** when
  only stub embeddings are active, unless the explicit
  `--allow-unsafe-stub-merge` flag is passed (intended for tests/demos).
- `EmbeddingProvider.is_stub` flag; `forge scan`, `forge run --dry-run`, and
  `forge status` now label their output as stub-based when applicable.

### Changed
- Folder skills are archived as **whole folders** (including scripts, references,
  and assets), never just their `SKILL.md`; no orphaned folder is left behind.
- README: documented folder-based skills, the `[dev]` extra for running tests,
  the stub safety guard, and an honest positioning of `loadout` (a static top-K
  prefilter for raw-API/custom workflows, not a replacement for a native agent's
  progressive skill loading).

### Fixed
- Corrected the GitHub repository URLs (clone command in README; `Homepage` and
  `Issues` in `pyproject.toml`) to `LAKITALKS/agent-maintenance`.

## [0.2.0]

- Ollama provider (local inference, auto-detected).
- Improved structural merge with section synthesis.
- `forge status` — read-only library health overview.

## [0.1.0]

- Initial release: `forge` (scan/run) and `loadout` (prepare), embedding-based
  similarity, LLM-assisted merge, dated archive.
