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
- Generates a compressed meta-skill per cluster (via Anthropic Claude, local Ollama, or structural fallback)
- Moves original files to a dated archive — **originals are never deleted**
- Enriches missing metadata

### `loadout` — Prepare for a task

Given a task description, assembles only the skills you actually need:

- Scores and ranks skills against your task semantically
- Selects the top-K most relevant ones
- Outputs a single `CONTEXT.md` or copies files to a `loadout/` directory

**When this is useful — and when it isn't.** `loadout` is aimed at raw-API,
custom-agent, and non-native workflows where *you* control which context goes
into the prompt and there is no built-in skill selection. It is a static,
semantic, top-K prefilter — nothing more. If you already use a standard-compliant
agent (e.g. Claude Code) that does **progressive skill loading** on its own,
`loadout` is not meant to replace that mechanism; the agent's native selection is
generally the better path there.

---

## Installation

`agent-maintenance` is not yet on PyPI. Install directly from the repository:

```bash
git clone https://github.com/LAKITALKS/agent-maintenance
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

# Development (tests, linting, type-checking — includes pytest + pytest-cov)
pip install -e ".[dev]"
```

Run the test suite with `pytest` once the `[dev]` extra is installed.

> **Safety note:** without the `[embeddings]` extra the tool falls back to
> deterministic *stub* embeddings whose similarity scores are **not** semantically
> meaningful. `forge scan` and `forge run --dry-run` still work (and label their
> output as stub-based), but a destructive `forge run` is **refused** unless you
> pass `--allow-unsafe-stub-merge` (intended for tests/demos only).

---

## Quickstart

```bash
# Health overview — read-only snapshot of your library
agent-maintenance forge status --skills-dir ./skills

# Scan — see what's redundant and which skills could be merged
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

Two on-disk layouts are supported and can be mixed freely in one directory:

**1. Legacy flat skills** — a standalone Markdown file `skills/<name>.md`:

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

**2. Folder skills** — the standard Agent Skills layout `skills/<name>/SKILL.md`,
optionally alongside scripts, references, or assets in the same folder:

```
skills/
├── code_review.md                 # flat skill
└── react_useeffect_patterns/      # folder skill
    ├── SKILL.md                    # parsed as the skill
    ├── reference.md               # travels with the skill when archived
    └── scripts/check.py
```

`SKILL.md` needs only minimal frontmatter (`name` and `description`); `tags` are
optional and their absence is never an error. If `name` is omitted it defaults to
the folder name. When a folder skill is archived, **the entire folder** is moved —
scripts and assets included — never just the `SKILL.md`.

Discovery is one level deep: only `skills/*.md` and `skills/<name>/SKILL.md` are
picked up. Hidden folders (including `.archive/`) and more deeply nested
`SKILL.md` files are ignored.

Skills without frontmatter are accepted — name defaults to the filename (or folder)
stem, description is inferred from the first heading.

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

## LLM providers

`forge run` resolves the best available LLM in this order:

| Priority | Provider | Requires |
|---|---|---|
| 1 | **Anthropic Claude** | `ANTHROPIC_API_KEY` + `pip install agent-maintenance[llm]` |
| 2 | **Ollama** (local) | Ollama running at `localhost:11434` — no API key, no extra install |
| 3 | **Structural fallback** | always available |

**Anthropic:**

```bash
pip install agent-maintenance[llm]
export ANTHROPIC_API_KEY="sk-ant-..."
agent-maintenance forge run --skills-dir ./skills
```

**Ollama:**

```bash
# Install Ollama: https://ollama.com
ollama pull llama3.2
ollama serve
# agent-maintenance auto-detects it — no config needed
agent-maintenance forge run --skills-dir ./skills
```

Override the Ollama server or model via environment variables:

```bash
export OLLAMA_HOST="http://myserver:11434"
export OLLAMA_MODEL="mistral"
```

The model can also be set via `llm_model` in `agent-maintenance.toml`.

---

## Safety guarantees

| Guarantee | How |
|---|---|
| Originals never deleted | `forge run` moves files to `.archive/YYYY-MM-DD/`, never `rm` |
| Folder skills stay intact | Folder skills are archived as whole folders — scripts and assets included, never just `SKILL.md` |
| No merge on meaningless data | Destructive `forge run` is refused under stub embeddings unless `--allow-unsafe-stub-merge` is passed |
| Preview before committing | `--dry-run` flag on every destructive command |
| Fallback on missing provider | Stub providers keep the tool functional without any API key |
| No key leakage | API keys are never logged, printed, or included in exceptions |

---

## Project layout

```
src/agent_maintenance/
├── cli/          # Typer-based commands: forge status, forge scan, forge run, loadout prepare
├── core/         # Shared: Skill model, Markdown+YAML parser, AppConfig
├── forge/        # reader · normalizer · comparator · clusterer · merger · archiver · writer
├── loadout/      # ranker · selector · writer
└── providers/    # Pluggable: EmbeddingProvider, LLMProvider (Anthropic, Ollama, stub) + factory
```

---

## What's not in v0.3

The following are intentionally out of scope:

- **Usage-frequency tracking** — no telemetry, no automatic scoring based on how often a skill is used
- **Historical success scoring** — skills are ranked by semantic similarity, not by past performance data
- **Adaptive ranking over time** — loadout selection is stateless; it does not learn from previous sessions
- **Additional LLM providers** — Anthropic and Ollama are supported; OpenAI is not
- **IDE integration** — no VS Code extension, no Claude Code hooks, no Cursor plugin
- **Cloud sync** — everything runs locally on your filesystem

---

## Quality

- **120 tests** across all core modules
- **CI** via GitHub Actions (Python 3.11 + 3.12, `pytest` + `ruff`)
- **Linter-clean** — passes `ruff` with no warnings

---

## Roadmap

- [x] Semantic similarity via sentence-transformers
- [x] LLM-assisted merge via Anthropic Claude
- [x] `forge run` with dry-run mode
- [x] Config file (`agent-maintenance.toml`)
- [x] Ollama provider (local inference, auto-detected)
- [x] `forge status` — read-only library health overview
- [x] Improved structural merge with section synthesis
- [x] Folder-format skills (`skills/<name>/SKILL.md`) with whole-folder archiving
- [x] Refuse destructive `forge run` under stub embeddings
- [ ] `loadout prepare` with LLM-ranked selection
- [ ] Plugin system for custom providers

---

## License

MIT
