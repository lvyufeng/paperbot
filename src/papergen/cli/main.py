"""Main CLI entry point for PaperGen."""

from pathlib import Path
from typing import Optional, List

import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from ..core.project import PaperProject
from ..core.config import config
from ..core.logging_config import setup_logging, get_logger

app = typer.Typer(
    name="papergen",
    help="AI-powered academic paper writing pipeline using Claude",
    add_completion=False,
)

console = Console()


@app.callback()
def callback(
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging"),
    log_file: Optional[Path] = typer.Option(None, "--log-file", help="Custom log file path"),
):
    """
    PaperGen - AI-powered academic paper writing pipeline.

    Use --debug to enable verbose logging.
    """
    # Set up logging
    if log_file is None:
        # Try to use project log file if in a project
        try:
            project_path = Path.cwd()
            if (project_path / ".papergen").exists():
                log_file = project_path / ".papergen" / "papergen.log"
        except Exception:
            pass

    level = "DEBUG" if debug else "INFO"
    setup_logging(log_file=log_file, level=level, enable_file=(log_file is not None))

    logger = get_logger()
    if debug:
        logger.debug("Debug mode enabled")



@app.command()
def init(
    topic: str = typer.Argument(..., help="Research topic or paper title"),
    template: str = typer.Option("ieee", help="LaTeX template (ieee, acm, springer)"),
    format: str = typer.Option("latex", help="Output format (latex, markdown)"),
    author: Optional[str] = typer.Option(None, help="Author name"),
    keywords: Optional[str] = typer.Option(None, help="Comma-separated keywords"),
    path: Optional[Path] = typer.Option(None, help="Project path (default: current directory)"),
):
    """Initialize a new paper project."""
    logger = get_logger()
    project_path = Path(path) if path else Path.cwd()

    logger.info(f"Initializing project: topic='{topic}', template={template}, format={format}, path={project_path}")

    # Check if already initialized
    if (project_path / ".papergen").exists():
        console.print("[yellow]Warning: Project already initialized in this directory.[/yellow]")
        logger.warning(f"Project already initialized at {project_path}")
        return

    # Prepare metadata
    metadata = {}
    if author:
        metadata['authors'] = [a.strip() for a in author.split(',')]
    if keywords:
        metadata['keywords'] = [k.strip() for k in keywords.split(',')]

    try:
        # Initialize project
        project = PaperProject(project_path)
        state = project.initialize(topic, template, format, metadata)

        logger.info(f"Project initialized successfully: project_id={state.project_id}")

        console.print(f"\n[green]✓[/green] Project initialized successfully!")
        console.print(f"[dim]Project ID:[/dim] {state.project_id}")
        console.print(f"[dim]Topic:[/dim] {topic}")
        console.print(f"[dim]Template:[/dim] {template}")
        console.print(f"[dim]Format:[/dim] {format}")

        console.print("\n[cyan]Next steps:[/cyan]")
        console.print("  1. Add research sources: [bold]papergen research add paper.pdf[/bold]")
        console.print("  2. Organize research: [bold]papergen research organize[/bold]")
        console.print("  3. Generate outline: [bold]papergen outline generate[/bold]")

    except Exception as e:
        logger.error(f"Failed to initialize project: {str(e)}", exc_info=True)
        console.print(f"[red]Error initializing project: {str(e)}[/red]")
        raise typer.Exit(1)


@app.command()
def status():
    """Show current project status."""
    project = _get_project()
    state = project.state

    console.print(f"\n[bold]Project Status[/bold]")
    console.print(f"[dim]Topic:[/dim] {state.topic}")
    console.print(f"[dim]Current Stage:[/dim] {state.current_stage}")
    console.print(f"[dim]Template:[/dim] {state.template}")
    console.print(f"[dim]Format:[/dim] {state.format}")

    # Stage status table
    console.print("\n[bold]Pipeline Stages:[/bold]")
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Stage", style="dim")
    table.add_column("Status")
    table.add_column("Started")
    table.add_column("Completed")

    for stage_name in ["research", "outline", "draft", "revise", "format"]:
        stage_info = state.stages.get(stage_name)
        if stage_info:
            # Status with color
            status = stage_info.status.value
            if status == "completed":
                status_display = f"[green]{status}[/green]"
            elif status == "in_progress":
                status_display = f"[yellow]{status}[/yellow]"
            elif status == "failed":
                status_display = f"[red]{status}[/red]"
            else:
                status_display = f"[dim]{status}[/dim]"

            started = stage_info.started_at.strftime("%Y-%m-%d %H:%M") if stage_info.started_at else "-"
            completed = stage_info.completed_at.strftime("%Y-%m-%d %H:%M") if stage_info.completed_at else "-"

            table.add_row(stage_name, status_display, started, completed)
        else:
            table.add_row(stage_name, "[dim]pending[/dim]", "-", "-")

    console.print(table)

    # Statistics
    console.print("\n[bold]Statistics:[/bold]")
    if project.has_research():
        extracted_dir = project.get_extracted_dir()
        source_count = len(list(extracted_dir.glob("*.json")))
        console.print(f"  Sources: {source_count}")

    if project.has_outline():
        console.print("  Outline: ✓")

    drafts_dir = project.get_drafts_dir()
    draft_count = len(list(drafts_dir.glob("*.md")))
    if draft_count > 0:
        console.print(f"  Drafts: {draft_count} sections")


@app.command()
def config_cmd(
    key: Optional[str] = typer.Argument(None, help="Configuration key"),
    value: Optional[str] = typer.Argument(None, help="Value to set"),
    show: bool = typer.Option(False, "--show", help="Show all configuration"),
):
    """View or modify configuration."""
    if show:
        # Show all configuration
        console.print("[bold]Current Configuration:[/bold]")
        import yaml
        console.print(yaml.dump(config._config, default_flow_style=False))
        return

    if key and value:
        # Set configuration
        config.set(key, value)
        console.print(f"[green]✓[/green] Set {key} = {value}")
    elif key:
        # Get configuration
        val = config.get(key)
        console.print(f"{key} = {val}")
    else:
        console.print("[yellow]Usage: papergen config <key> [value] or --show[/yellow]")


def _get_project() -> PaperProject:
    """Get current project or exit if not found."""
    project_root = PaperProject.find_project_root()

    if project_root is None:
        console.print("[red]Error: Not in a papergen project directory.[/red]")
        console.print("Run [bold]papergen init[/bold] to initialize a project.")
        raise typer.Exit(1)

    project = PaperProject(project_root)

    # Load project-specific config
    config.load_project_config(project_root)

    return project


@app.command()
def chat():
    """Start interactive chat mode for paper writing assistance."""
    from ..interactive.repl import PaperGenREPL
    repl = PaperGenREPL()
    repl.run()


# Subcommands
from . import research as research_module
from . import outline as outline_module
from . import draft as draft_module
from . import revise as revise_module
from . import format as format_module
from . import discover as discover_module
app.add_typer(research_module.app, name="research")
app.add_typer(outline_module.app, name="outline")
app.add_typer(draft_module.app, name="draft")
app.add_typer(revise_module.app, name="revise")
app.add_typer(format_module.app, name="format")
app.add_typer(discover_module.app, name="discover")


if __name__ == "__main__":
    app()
