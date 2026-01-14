"""Research CLI commands."""

from pathlib import Path
from typing import Optional, List
from datetime import datetime
import json
import uuid

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..core.project import PaperProject
from ..core.state import Source, SourceType
from ..sources.pdf_extractor import PDFExtractor
from ..sources.web_extractor import WebExtractor
from ..sources.text_extractor import TextExtractor
from ..sources.organizer import ResearchOrganizer

app = typer.Typer(name="research", help="Manage research sources")
console = Console()


def _get_project() -> PaperProject:
    """Get current project or exit."""
    from ..cli.main import _get_project as get_proj
    return get_proj()


@app.command("add")
def add_sources(
    files: List[Path] = typer.Argument(..., help="Files to add as sources"),
    url: Optional[str] = typer.Option(None, help="URL to add as source"),
    source_type: Optional[str] = typer.Option(None, help="Source type (pdf, text, note)"),
):
    """Add research sources to the project."""
    project = _get_project()

    if url:
        # Add URL source
        _add_url_source(project, url)
        return

    # Add file sources
    for file_path in files:
        if not file_path.exists():
            console.print(f"[red]Error: File not found: {file_path}[/red]")
            continue

        _add_file_source(project, file_path, source_type)


def _add_file_source(project: PaperProject, file_path: Path, source_type: Optional[str] = None):
    """Add a file source."""
    # Determine source type
    if source_type:
        stype = SourceType(source_type.lower())
    else:
        # Auto-detect from extension
        if file_path.suffix.lower() == '.pdf':
            stype = SourceType.PDF
        elif file_path.suffix.lower() in ['.txt', '.md', '.markdown']:
            stype = SourceType.TEXT
        else:
            console.print(f"[yellow]Warning: Unknown file type {file_path.suffix}, treating as text[/yellow]")
            stype = SourceType.TEXT

    # Generate source ID
    source_id = f"source_{uuid.uuid4().hex[:8]}"

    # Copy file to sources directory
    if stype == SourceType.PDF:
        dest_dir = project.get_sources_dir() / "pdfs"
    else:
        dest_dir = project.get_sources_dir() / "notes"

    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_file = dest_dir / file_path.name

    # Copy file if not already there
    if not dest_file.exists():
        import shutil
        shutil.copy2(file_path, dest_file)

    extracted_file = project.get_extracted_dir() / f"{source_id}.json"

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task(f"Extracting {file_path.name}...", total=None)

        # Extract content
        try:
            if stype == SourceType.PDF:
                extractor = PDFExtractor()
                extracted = extractor.extract(dest_file)
            else:
                extractor = TextExtractor()
                extracted = extractor.extract(dest_file)

            # Add source ID and type
            extracted["id"] = source_id
            extracted["type"] = stype.value
            extracted["original_path"] = str(dest_file)
            extracted["added_at"] = datetime.now().isoformat()

            # Save extracted content
            with open(extracted_file, 'w') as f:
                json.dump(extracted, f, indent=2, default=str)

            # Update index
            _update_source_index(project, source_id, extracted)

            progress.update(task, completed=True)
            console.print(f"[green]✓[/green] Added {file_path.name} as {source_id}")

        except Exception as e:
            console.print(f"[red]Error extracting {file_path.name}: {str(e)}[/red]")


def _add_url_source(project: PaperProject, url: str):
    """Add a URL source."""
    source_id = f"source_{uuid.uuid4().hex[:8]}"
    extracted_file = project.get_extracted_dir() / f"{source_id}.json"

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task(f"Fetching {url}...", total=None)

        try:
            extractor = WebExtractor()
            extracted = extractor.extract(url)

            # Add source info
            extracted["id"] = source_id
            extracted["type"] = SourceType.WEB.value
            extracted["original_path"] = url
            extracted["added_at"] = datetime.now().isoformat()

            # Save extracted content
            with open(extracted_file, 'w') as f:
                json.dump(extracted, f, indent=2, default=str)

            # Update index
            _update_source_index(project, source_id, extracted)

            progress.update(task, completed=True)
            console.print(f"[green]✓[/green] Added {url} as {source_id}")

        except Exception as e:
            console.print(f"[red]Error fetching {url}: {str(e)}[/red]")


def _update_source_index(project: PaperProject, source_id: str, extracted: dict):
    """Update the source index file."""
    index_file = project.get_extracted_dir() / "index.json"

    # Load existing index
    if index_file.exists():
        with open(index_file, 'r') as f:
            index = json.load(f)
    else:
        index = {"sources": []}

    # Add new source to index
    source_entry = {
        "id": source_id,
        "type": extracted["type"],
        "original_path": extracted["original_path"],
        "extracted_path": str(project.get_extracted_dir() / f"{source_id}.json"),
        "added_at": extracted["added_at"],
        "metadata": extracted.get("metadata", {}),
        "extraction_status": "success",
    }

    index["sources"].append(source_entry)

    # Save index
    with open(index_file, 'w') as f:
        json.dump(index, f, indent=2)


@app.command("organize")
def organize_research(
    focus: Optional[str] = typer.Option(None, help="Focus areas (e.g., 'methodology, results')"),
    use_ai: bool = typer.Option(True, help="Use AI for organization (requires API key)"),
):
    """Organize research sources using AI."""
    project = _get_project()
    state = project.state

    # Check if we have sources
    extracted_dir = project.get_extracted_dir()
    source_files = list(extracted_dir.glob("*.json"))
    source_files = [f for f in source_files if f.name != "index.json"]

    if not source_files:
        console.print("[yellow]No research sources found. Add sources first with 'papergen research add'[/yellow]")
        return

    console.print(f"Found {len(source_files)} sources to organize...")

    # Load all sources
    sources = []
    for source_file in source_files:
        with open(source_file, 'r') as f:
            sources.append(json.load(f))

    # Initialize organizer with Claude if requested
    organizer = None
    if use_ai:
        try:
            from ..ai.claude_client import ClaudeClient
            from ..core.config import config

            console.print("[dim]Initializing AI...[/dim]")
            claude_client = ClaudeClient()
            organizer = ResearchOrganizer(claude_client)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not initialize AI ({str(e)}). Using basic organization.[/yellow]")
            organizer = ResearchOrganizer()
    else:
        organizer = ResearchOrganizer()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Organizing research with AI...", total=None)

        # Organize sources
        organized = organizer.organize(sources, focus or "", state.topic)

        # Save organized research
        research_dir = project.get_research_dir()
        output_file = research_dir / "organized_notes.md"

        with open(output_file, 'w') as f:
            f.write(organized)

        progress.update(task, completed=True)

    console.print(f"[green]✓[/green] Research organized and saved to {output_file}")

    if organizer.claude_client:
        console.print(f"[dim]Organized using AI (Claude)[/dim]")
    else:
        console.print(f"[dim]Note: Used basic organization. Set ANTHROPIC_API_KEY for AI-powered organization.[/dim]")

    # Mark research stage as completed
    state.mark_stage_completed("research")
    project.save_state()


@app.command("list")
def list_sources():
    """List all research sources."""
    project = _get_project()

    index_file = project.get_extracted_dir() / "index.json"
    if not index_file.exists():
        console.print("[yellow]No sources found.[/yellow]")
        return

    with open(index_file, 'r') as f:
        index = json.load(f)

    sources = index.get("sources", [])

    if not sources:
        console.print("[yellow]No sources found.[/yellow]")
        return

    console.print(f"\n[bold]Research Sources ({len(sources)} total):[/bold]\n")

    for source in sources:
        console.print(f"[cyan]{source['id']}[/cyan]")
        console.print(f"  Type: {source['type']}")
        console.print(f"  Title: {source.get('metadata', {}).get('title', 'N/A')}")
        console.print(f"  Added: {source['added_at']}")
        console.print()


if __name__ == "__main__":
    app()
