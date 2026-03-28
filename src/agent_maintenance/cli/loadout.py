"""CLI commands for the Loadout domain."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from agent_maintenance.core.config import load_config
from agent_maintenance.core.models import LoadoutResult
from agent_maintenance.forge.reader import SkillReader
from agent_maintenance.loadout.selector import SkillSelector
from agent_maintenance.loadout.writer import LoadoutWriter
from agent_maintenance.providers.factory import get_embedding_provider

app = typer.Typer(no_args_is_help=True)
console = Console()


def _require_dir(path: Path) -> None:
    if not path.is_dir():
        console.print(f"[red]Error:[/red] skills directory not found: [cyan]{path}[/cyan]")
        raise typer.Exit(code=1)


@app.command()
def prepare(
    task: Annotated[
        str,
        typer.Option("--task", "-t", help="Natural-language description of your task."),
    ],
    skills_dir: Annotated[
        Path | None,
        typer.Option("--skills-dir", "-s", help="Directory containing skill Markdown files."),
    ] = None,
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output directory for the generated loadout."),
    ] = None,
    top_k: Annotated[
        int | None,
        typer.Option("--top-k", "-k", min=1, help="Number of skills to include."),
    ] = None,
    context_md: Annotated[
        bool,
        typer.Option("--context-md/--no-context-md", help="Write a single CONTEXT.md file."),
    ] = True,
) -> None:
    """Select the most relevant skills for a task and write a focused loadout."""
    config = load_config().apply_overrides(
        skills_dir=skills_dir,
        output_dir=output,
        top_k=top_k,
    )
    _require_dir(config.skills_dir)

    reader = SkillReader(config.skills_dir)
    provider = get_embedding_provider(config.embedding_model)
    selector = SkillSelector(embedding_provider=provider, top_k=config.top_k)
    writer = LoadoutWriter()

    with console.status("[bold green]Reading skills…"):
        skills = reader.read_all()

    if not skills:
        console.print("[yellow]No skills found. Nothing to prepare.[/yellow]")
        raise typer.Exit()

    with console.status("[bold green]Ranking skills for task…"):
        selected = selector.select(task, skills)

    result = LoadoutResult(task_description=task, selected_skills=selected)

    table = Table(title=f"Loadout — top {len(selected)} of {len(skills)} skill(s)", show_lines=True)
    table.add_column("#", style="dim", width=3)
    table.add_column("Skill", style="cyan")
    table.add_column("Tags")
    table.add_column("Description")
    for i, skill in enumerate(selected, 1):
        table.add_row(
            str(i),
            skill.name,
            ", ".join(skill.tags) or "-",
            skill.metadata.description or "-",
        )
    console.print()
    console.print(table)

    if context_md:
        out_file = config.output_dir / "CONTEXT.md"
        writer.write_context_md(result, out_file)
        console.print(f"\n[green]✓[/green] Written to [cyan]{out_file}[/cyan]")
    else:
        writer.write_loadout_dir(result, config.output_dir)
        console.print(f"\n[green]✓[/green] Skills copied to [cyan]{config.output_dir}[/cyan]")
