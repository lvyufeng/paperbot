"""Draft CLI commands."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.markdown import Markdown

from ..core.project import PaperProject
from ..document.outline import Outline
from ..document.section import SectionManager
from ..document.citation import CitationManager

app = typer.Typer(name="draft", help="Draft paper sections")
console = Console()


def _get_project() -> PaperProject:
    """Get current project or exit."""
    from ..cli.main import _get_project as get_proj
    return get_proj()


@app.command()
def draft_section(
    section: str = typer.Argument(..., help="Section ID to draft (e.g., 'introduction')"),
    guidance: Optional[str] = typer.Option(None, help="Additional guidance for drafting"),
    use_ai: bool = typer.Option(True, help="Use AI for drafting (requires API key)"),
):
    """Draft a specific section."""
    project = _get_project()
    state = project.state

    # Check if outline exists
    outline_file = project.get_outline_dir() / "outline.json"
    if not outline_file.exists():
        console.print("[red]Error: No outline found. Run 'papergen outline generate' first.[/red]")
        raise typer.Exit(1)

    # Load outline
    outline = Outline.from_json_file(outline_file)

    # Find section
    section_obj = outline.get_section_by_id(section)
    if not section_obj:
        console.print(f"[red]Error: Section '{section}' not found in outline.[/red]")
        console.print("\n[dim]Available sections:[/dim]")
        for s in outline.get_all_sections_flat():
            console.print(f"  - {s.id}")
        raise typer.Exit(1)

    # Load research
    research_file = project.get_research_dir() / "organized_notes.md"
    research_text = ""
    if research_file.exists():
        with open(research_file, 'r') as f:
            research_text = f.read()

    if not use_ai:
        console.print("[yellow]AI disabled. Cannot draft without AI. Please enable AI.[/yellow]")
        return

    # Initialize managers
    try:
        from ..ai.claude_client import ClaudeClient
        from ..core.config import config

        console.print("[dim]Initializing AI...[/dim]")
        claude_client = ClaudeClient()
        citation_manager = CitationManager(style=config.get_citation_style())
        section_manager = SectionManager(
            project.root_path,
            claude_client,
            citation_manager
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(
                f"Drafting {section_obj.title}... (target: {section_obj.word_count_target} words)",
                total=None
            )

            # Draft section
            draft = section_manager.draft_section(
                section=section_obj,
                research_text=research_text,
                guidance=guidance or ""
            )

            # Save draft
            draft_file = section_manager.save_draft(draft)

            # Save citation manager
            citations_file = project.get_research_dir() / "citations.json"
            citation_manager.save(citations_file)

            progress.update(task, completed=True)

        console.print(f"\n[green]✓[/green] Drafted {section_obj.title}")
        console.print(f"[dim]Word count:[/dim] {draft.word_count} / {section_obj.word_count_target}")
        console.print(f"[dim]Citations:[/dim] {len(draft.citation_keys)}")
        console.print(f"[dim]Saved to:[/dim] {draft_file}")

        # Show preview
        _show_draft_preview(draft.content)

    except Exception as e:
        console.print(f"[red]Error drafting section: {str(e)}[/red]")
        raise typer.Exit(1)


@app.command("all")
def draft_all(
    skip_existing: bool = typer.Option(True, help="Skip sections that are already drafted"),
    use_ai: bool = typer.Option(True, help="Use AI for drafting"),
):
    """Draft all sections in the outline."""
    project = _get_project()

    # Check if outline exists
    outline_file = project.get_outline_dir() / "outline.json"
    if not outline_file.exists():
        console.print("[red]Error: No outline found. Run 'papergen outline generate' first.[/red]")
        raise typer.Exit(1)

    # Load outline
    outline = Outline.from_json_file(outline_file)

    if not use_ai:
        console.print("[yellow]AI disabled. Cannot draft without AI.[/yellow]")
        return

    # Initialize managers
    try:
        from ..ai.claude_client import ClaudeClient
        from ..core.config import config

        claude_client = ClaudeClient()
        citation_manager = CitationManager(style=config.get_citation_style())
        section_manager = SectionManager(
            project.root_path,
            claude_client,
            citation_manager
        )

        # Load research
        research_file = project.get_research_dir() / "organized_notes.md"
        research_text = ""
        if research_file.exists():
            with open(research_file, 'r') as f:
                research_text = f.read()

        # Get all sections
        all_sections = outline.get_all_sections_flat()

        # Filter out existing if skip_existing
        sections_to_draft = []
        for sect in all_sections:
            if skip_existing and section_manager.get_draft_content(sect.id):
                console.print(f"[dim]Skipping {sect.title} (already drafted)[/dim]")
                continue
            sections_to_draft.append(sect)

        if not sections_to_draft:
            console.print("[yellow]All sections already drafted.[/yellow]")
            return

        console.print(f"\n[bold]Drafting {len(sections_to_draft)} sections...[/bold]\n")

        # Draft each section
        for i, sect in enumerate(sections_to_draft, 1):
            console.print(f"[cyan]({i}/{len(sections_to_draft)})[/cyan] {sect.title}")

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task(f"Drafting...", total=None)

                draft = section_manager.draft_section(
                    section=sect,
                    research_text=research_text,
                    guidance=""
                )

                section_manager.save_draft(draft)
                progress.update(task, completed=True)

            console.print(f"  [green]✓[/green] {draft.word_count} words, {len(draft.citation_keys)} citations\n")

        # Save citations
        citations_file = project.get_research_dir() / "citations.json"
        citation_manager.save(citations_file)

        console.print(f"[green]✓[/green] All sections drafted!")

        # Show statistics
        stats = section_manager.get_statistics()
        console.print(f"\n[bold]Statistics:[/bold]")
        console.print(f"  Sections: {stats['sections_drafted']}")
        console.print(f"  Total words: {stats['total_words']}")
        console.print(f"  Citations: {stats['total_citations']}")

        # Mark stage as completed
        state.mark_stage_completed("draft")
        project.save_state()

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)


@app.command("show")
def show_draft(
    section: str = typer.Argument(..., help="Section ID to show"),
    format: str = typer.Option("preview", help="Output format (preview, full, markdown)"),
):
    """Show a drafted section."""
    project = _get_project()

    section_manager = SectionManager(project.root_path)
    draft = section_manager.load_draft(section)

    if not draft:
        console.print(f"[yellow]No draft found for section: {section}[/yellow]")
        console.print("\n[dim]Available drafts:[/dim]")
        for draft_id in section_manager.list_drafts():
            console.print(f"  - {draft_id}")
        return

    console.print(f"\n[bold cyan]{draft.metadata.get('section_title', section)}[/bold cyan]")
    console.print(f"[dim]Version {draft.version} • {draft.word_count} words • {len(draft.citation_keys)} citations[/dim]\n")

    if format == "preview":
        # Show first 500 characters
        preview = draft.content[:500]
        if len(draft.content) > 500:
            preview += "\n\n[... content truncated ...]"
        console.print(Markdown(preview))
        console.print(f"\n[dim]Use --format full to see complete content[/dim]")

    elif format == "full":
        console.print(Markdown(draft.content))

    elif format == "markdown":
        console.print(draft.content)

    else:
        console.print(f"[red]Unknown format: {format}[/red]")


@app.command("review")
def review_draft(
    section: str = typer.Argument(..., help="Section ID to review"),
):
    """Get AI review of a drafted section."""
    project = _get_project()

    section_manager = SectionManager(project.root_path)

    if not section_manager.get_draft_content(section):
        console.print(f"[yellow]No draft found for section: {section}[/yellow]")
        return

    try:
        from ..ai.claude_client import ClaudeClient

        console.print("[dim]Initializing AI...[/dim]")
        claude_client = ClaudeClient()
        section_manager.claude_client = claude_client

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"Reviewing {section}...", total=None)

            review = section_manager.review_section(section)

            progress.update(task, completed=True)

        console.print(f"\n[bold]Review of {section}:[/bold]\n")
        console.print(Markdown(review))

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")


@app.command("list")
def list_drafts():
    """List all drafted sections."""
    project = _get_project()

    section_manager = SectionManager(project.root_path)
    drafts = section_manager.list_drafts()

    if not drafts:
        console.print("[yellow]No drafts found.[/yellow]")
        return

    console.print(f"\n[bold]Drafted Sections ({len(drafts)} total):[/bold]\n")

    for section_id in sorted(drafts):
        draft = section_manager.load_draft(section_id)
        if draft:
            title = draft.metadata.get('section_title', section_id)
            console.print(f"[cyan]{section_id}[/cyan] - {title}")
            console.print(f"  Words: {draft.word_count}, Citations: {len(draft.citation_keys)}, Version: {draft.version}")


@app.command("stats")
def show_statistics():
    """Show drafting statistics."""
    project = _get_project()

    section_manager = SectionManager(project.root_path)
    stats = section_manager.get_statistics()

    console.print("\n[bold]Drafting Statistics:[/bold]\n")
    console.print(f"  Sections drafted: {stats['sections_drafted']}")
    console.print(f"  Total words: {stats['total_words']}")
    console.print(f"  Total citations: {stats['total_citations']}")
    console.print(f"  Average words/section: {stats['average_words_per_section']}")


def _show_draft_preview(content: str, max_lines: int = 10):
    """Show a preview of drafted content."""
    lines = content.split('\n')
    preview_lines = lines[:max_lines]

    console.print("\n[dim]Preview:[/dim]")
    console.print(Panel(
        Markdown('\n'.join(preview_lines)),
        title="Draft Preview",
        border_style="dim"
    ))

    if len(lines) > max_lines:
        console.print(f"[dim]... and {len(lines) - max_lines} more lines[/dim]")


if __name__ == "__main__":
    app()
