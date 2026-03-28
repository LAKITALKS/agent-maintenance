"""CLI commands for the Forge domain."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from agent_maintenance.core.config import load_config
from agent_maintenance.forge.archiver import SkillArchiver
from agent_maintenance.forge.clusterer import cluster_merge_candidates
from agent_maintenance.forge.comparator import SkillComparator
from agent_maintenance.forge.merger import SkillMerger
from agent_maintenance.forge.normalizer import SkillNormalizer
from agent_maintenance.forge.reader import SkillReader
from agent_maintenance.forge.writer import write_skill_file
from agent_maintenance.providers.factory import get_embedding_provider, get_llm_provider

app = typer.Typer(no_args_is_help=True)
console = Console()


def _require_dir(path: Path) -> None:
    if not path.is_dir():
        console.print(f"[red]Error:[/red] skills directory not found: [cyan]{path}[/cyan]")
        raise typer.Exit(code=1)


@app.command()
def scan(
    skills_dir: Annotated[
        Path | None,
        typer.Option("--skills-dir", "-s", help="Directory containing skill Markdown files."),
    ] = None,
    threshold: Annotated[
        float | None,
        typer.Option("--threshold", "-t", help="Similarity threshold (0.0–1.0)."),
    ] = None,
) -> None:
    """Scan a skill library and report redundancy / merge candidates."""
    config = load_config().apply_overrides(skills_dir=skills_dir, similarity_threshold=threshold)
    _require_dir(config.skills_dir)

    reader = SkillReader(config.skills_dir)
    provider = get_embedding_provider(config.embedding_model)
    comparator = SkillComparator(embedding_provider=provider, threshold=config.similarity_threshold)

    with console.status("[bold green]Reading skills…"):
        skills = reader.read_all()

    console.print(
        f"\n[bold]Found {len(skills)} skill(s)[/bold] in [cyan]{config.skills_dir}[/cyan]\n"
    )

    if not skills:
        console.print(
            "[yellow]No skill files found. Add .md files to the skills directory.[/yellow]"
        )
        raise typer.Exit()

    table = Table(title="Skills", show_lines=True)
    table.add_column("Name", style="cyan")
    table.add_column("Tags")
    table.add_column("Description")
    for skill in skills:
        table.add_row(
            skill.name,
            ", ".join(skill.tags) or "-",
            skill.metadata.description or "-",
        )
    console.print(table)

    with console.status("[bold green]Comparing skills…"):
        candidates = comparator.find_merge_candidates(skills)

    if candidates:
        clusters = cluster_merge_candidates(skills, candidates)
        console.print(
            f"\n[bold yellow]⚠  {len(candidates)} merge candidate pair(s) "
            f"in {len(clusters)} group(s):[/bold yellow]\n"
        )
        for i, cluster in enumerate(clusters, 1):
            names = " + ".join(f"[cyan]{s.name}[/cyan]" for s in cluster)
            console.print(f"  Group {i}: {names}")
        console.print(
            "\n[dim]Run [bold]forge run[/bold] to merge and archive these groups.[/dim]"
        )
    else:
        console.print("[green]✓ No merge candidates found above the threshold.[/green]")


@app.command()
def run(
    skills_dir: Annotated[
        Path | None,
        typer.Option("--skills-dir", "-s", help="Directory containing skill Markdown files."),
    ] = None,
    archive_dir: Annotated[
        Path | None,
        typer.Option("--archive-dir", "-a", help="Directory where archived skills will be moved."),
    ] = None,
    threshold: Annotated[
        float | None,
        typer.Option("--threshold", "-t", help="Similarity threshold for merge candidates."),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Preview all actions without writing or moving any files."),
    ] = False,
) -> None:
    """Run a full forge pass: merge similar skills, archive originals, write meta-skills.

    For each cluster of similar skills, a consolidated meta-skill is generated
    and written to the skills directory. The original files are moved to the
    archive directory — never deleted.

    Use --dry-run to preview all planned actions without touching the filesystem.
    """
    config = load_config().apply_overrides(
        skills_dir=skills_dir,
        archive_dir=archive_dir,
        similarity_threshold=threshold,
    )
    _require_dir(config.skills_dir)

    reader = SkillReader(config.skills_dir)
    normalizer = SkillNormalizer()
    embed_provider = get_embedding_provider(config.embedding_model)
    llm_provider = get_llm_provider(config.llm_model)
    comparator = SkillComparator(
        embedding_provider=embed_provider, threshold=config.similarity_threshold
    )
    merger = SkillMerger(llm_provider=llm_provider)
    archiver = SkillArchiver(config.archive_dir)

    # ── 1. Read & enrich ────────────────────────────────────────────────────
    with console.status("[bold green]Reading skills…"):
        skills = reader.read_all()

    if not skills:
        console.print("[yellow]No skills found. Nothing to do.[/yellow]")
        raise typer.Exit()

    enriched = [normalizer.enrich_metadata(s) for s in skills]
    console.print(f"\n[bold]Forge run[/bold] — {len(enriched)} skill(s) loaded")
    if dry_run:
        console.print("[dim](dry-run — no files will be written or moved)[/dim]")
    console.print()

    # ── 2. Find candidates & cluster ────────────────────────────────────────
    with console.status("[bold green]Comparing skills…"):
        candidates = comparator.find_merge_candidates(enriched)

    if not candidates:
        console.print("[green]✓[/green] No merge candidates found. Library is clean.")
        raise typer.Exit()

    clusters = cluster_merge_candidates(enriched, candidates)
    console.print(
        f"[yellow]Found {len(clusters)} merge group(s)[/yellow] "
        f"({len(candidates)} candidate pair(s))\n"
    )

    # ── 3. Process each cluster ─────────────────────────────────────────────
    meta_skills_created = 0
    originals_archived = 0

    for i, cluster in enumerate(clusters, 1):
        names = ", ".join(s.name for s in cluster)
        console.print(f"[bold]Group {i}:[/bold] {names}")

        # Generate meta-skill
        with console.status(f"  Generating meta-skill for group {i}…"):
            meta_skill = merger.merge(cluster)

        merge_method = meta_skill.raw_frontmatter.get("merge_method", "unknown")
        method_label = (
            "[dim](structural — configure an LLM provider for a compressed summary)[/dim]"
            if merge_method == "structural"
            else "[green](LLM-generated)[/green]"
        )

        dest_path = config.skills_dir / f"{meta_skill.name}.md"
        console.print(f"  → Meta-skill: [cyan]{dest_path.name}[/cyan] {method_label}")

        # List originals to archive
        to_archive = [s.source_path for s in cluster if s.source_path and s.source_path.exists()]
        for p in to_archive:
            console.print(f"  → Archive:    [dim]{p.name}[/dim]")

        if not dry_run:
            write_skill_file(meta_skill, dest_path)
            archived_paths = archiver.archive_many(to_archive)
            meta_skills_created += 1
            originals_archived += len(archived_paths)
            console.print(
                f"  [green]✓[/green] Written + {len(archived_paths)} original(s) archived"
            )

        console.print()

    # ── 4. Summary ──────────────────────────────────────────────────────────
    if dry_run:
        console.print(
            f"[dim]dry-run complete — would create {len(clusters)} meta-skill(s) "
            f"and archive {sum(len(c) for c in clusters)} original(s)[/dim]"
        )
    else:
        console.print(
            f"[green]✓ Forge run complete.[/green] "
            f"{meta_skills_created} meta-skill(s) created, "
            f"{originals_archived} original(s) archived."
        )
