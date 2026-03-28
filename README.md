# agent-maintenance

> A small, sharp CLI tool for maintaining local skill libraries used by coding agents.

Works alongside Claude Code, Cursor, Aider, or any agent-based setup —
without locking you into a specific framework or IDE.

---

## The problem it solves

When you work with coding agents over time, your skill and rule files accumulate:

- **Skill decay** — outdated instructions that no longer reflect how you work
- **Redundancy** — three files that say the same thing about React hooks or API design
- **Context poisoning** — loading 40 skills into every session, most of them irrelevant
- **Library bloat** — a `skills/` folder that nobody wants to curate manually

`agent-maintenance` handles the curation for you.

---

## Two modes

### `forge` — Clean your skill library

Scans a directory of skill/rule/Markdown files and finds overlap:

- Detects similar and redundant skills via embedding-based semantic similarity
- Groups merge candidates into clusters
- Generates a compressed meta-skill per cluster (via Anthropic Claude or structural fallback)
- Moves original files to a dated archive — **originals are never deleted**
- Enriches missing metadata

### `loadout` — Prepare for a task

Given a task description, assembles only the skills you actually need:

- Scores and ranks skills against your task semantically
- Selects the top-K most relevant ones
- Outputs a single `CONTEXT.md` or copies files to a `loadout/` directory

---

## Installation

`agent-maintenance` is not yet on PyPI. Install directly from the repository:

```bash
git clone https://github.com/lazarosvarvatis/agent-maintenance
cd agent-maintenance
pip install -e .
```

**Optional extras:**

```bash
# Semantic similarity via local sentence-transformers (~80 MB model download)
pip install -e ".[embeddings]"

# LLM-compressed meta-skills via Anthropic Claude
pip install -e ".[llm]"

# Everything
pip install -e ".[embeddings,llm]"
```

---

## Quickstart

```bash
# Scan your skill library — see what's redundant
agent-maintenance forge scan --skills-dir ./skills

# Dry run — preview what forge run would do, without touching files
agent-maintenance forge run --skills-dir ./skills --dry-run

# Full forge pass — merge, archive, write meta-skills
agent-maintenance forge run --skills-dir ./skills --archive-dir .archive

# Prepare a focused loadout for a specific task
agent-maintenance loadout prepare \
  --task "Refactor the authentication module" \
  --skills-dir ./skills \
  --top-k 5
```

---

## Demo: the React hooks merge

The `examples/skills/` directory ships with three intentionally similar React skills:

| File | Focus |
|---|---|
| `react_useeffect_patterns.md` | Correct patterns, deps, cleanup |
| `react_hooks_debugging.md` | Stale closures, infinite loops, diagnosis |
| `react_component_lifecycle.md` | Mount/update/unmount timing, async safety |

Run the demo:

```bash
# Step 1 — see the cluster
agent-maintenance forge scan --skills-dir examples/skills

# Step 2 — preview the merge
agent-maintenance forge run --skills-dir examples/skills --dry-run

# Step 3 — run it (set key first for LLM-compressed output)
export ANTHROPIC_API_KEY="sk-ant-..."
agent-maintenance forge run \
  --skills-dir examples/skills \
  --archive-dir .archive
```

**What you get:**

- A new `useeffect_merged.md` in your skills directory — named after the most specific shared tag
- Three originals moved to `.archive/YYYY-MM-DD/`
- YAML frontmatter with `source_skills`, `merged_by`, `merge_method`

Without a key or the `[llm]` extra the tool still works — it produces a structural
merge and notes `merge_method: structural` in the frontmatter.

---

## Skill file format

Skills are Markdown files with an optional YAML frontmatter block:

```markdown
---
name: react_useeffect_patterns
description: Correct patterns for useEffect — dependencies, cleanup, and avoiding stale closures
tags: [react, hooks, useeffect, typescript, frontend]
version: "1.0"
---

# React useEffect Patterns

...content...
```

Skills without frontmatter are accepted — name defaults to the filename stem,
description is inferred from the first heading.

---

## Configuration file

Create `agent-maintenance.toml` in your project root to set defaults:

```toml
# agent-maintenance.toml
skills_dir = "skills"
archive_dir = ".archive"
output_dir  = "loadout"
top_k       = 5
similarity_threshold = 0.75

# LLM model for forge merges (default: claude-haiku-4-5-20251001)
# llm_model = "claude-sonnet-4-6"

# Embedding model for similarity (default: all-MiniLM-L6-v2)
# embedding_model = "all-MiniLM-L6-v2"
```

CLI flags always override the config file.

---

## LLM provider

`forge run` uses Anthropic Claude when `ANTHROPIC_API_KEY` is set and the
`[llm]` extra is installed. Otherwise it falls back to a structural merge.

```bash
pip install agent-maintenance[llm]
export ANTHROPIC_API_KEY="sk-ant-..."
agent-maintenance forge run --skills-dir ./skills
```

The model can be overridden via `llm_model` in `agent-maintenance.toml`.

---

## Safety guarantees

| Guarantee | How |
|---|---|
| Originals never deleted | `forge run` moves files to `.archive/YYYY-MM-DD/`, never `rm` |
| Preview before committing | `--dry-run` flag on every destructive command |
| Fallback on missing provider | Stub providers keep the tool functional without any API key |
| No key leakage | API keys are never logged, printed, or included in exceptions |

---

## Project layout

```
src/agent_maintenance/
├── cli/          # Typer-based commands: forge scan, forge run, loadout prepare
├── core/         # Shared: Skill model, Markdown+YAML parser, AppConfig
├── forge/        # reader · normalizer · comparator · clusterer · merger · archiver · writer
├── loadout/      # ranker · selector · writer
└── providers/    # Pluggable: EmbeddingProvider, LLMProvider + factory
```

---

## What's not in v0.1

This is a focused first release. The following are intentionally out of scope:

- **Usage-frequency tracking** — no telemetry, no automatic scoring based on how often a skill is used
- **Historical success scoring** — skills are ranked by semantic similarity, not by past performance data
- **Adaptive ranking over time** — loadout selection is stateless; it does not learn from previous sessions
- **Additional LLM providers** — only Anthropic Claude is supported; Ollama and OpenAI are not yet wired in
- **IDE integration** — no VS Code extension, no Claude Code hooks, no Cursor plugin
- **Cloud sync** — everything runs locally on your filesystem

These may come in future releases. For now, the tool is deliberately small and local.

---

## Quality

- **66 tests** across all core modules
- **CI** via GitHub Actions (Python 3.11 + 3.12, `pytest` + `ruff`)
- **Linter-clean** — passes `ruff` with no warnings

---

## Roadmap

- [x] Semantic similarity via sentence-transformers
- [x] LLM-assisted merge via Anthropic Claude
- [x] `forge run` with dry-run mode
- [x] Config file (`agent-maintenance.toml`)
- [ ] Additional LLM providers (Ollama, OpenAI)
- [ ] `loadout prepare` with LLM-ranked selection
- [ ] Plugin system for custom providers

---

## License

MIT
