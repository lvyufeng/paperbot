"""Revise CLI commands."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.markdown import Markdown

from ..core.project import PaperProject
from ..document.section import SectionManager
from ..document.citation import CitationManager

app = typer.Typer(name="revise", help="Revise paper sections")
console = Console()


def _get_project() -> PaperProject:
    """Get current project or exit."""
    from ..cli.main import _get_project as get_proj
    return get_proj()


@app.command()
def revise_section(
    section: str = typer.Argument(..., help="Section ID to revise"),
    feedback: Optional[str] = typer.Option(None, help="Feedback for revision"),
    interactive: bool = typer.Option(False, help="Interactive mode with prompts"),
    use_ai: bool = typer.Option(True, help="Use AI for revision"),
):
    """Revise a section based on feedback."""
    project = _get_project()

    # Check if draft exists
    section_manager = SectionManager(project.root_path)
    draft = section_manager.load_draft(section)

    if not draft:
        console.print(f"[red]Error: No draft found for section '{section}'.[/red]")
        console.print("\n[dim]Available drafts:[/dim]")
        for draft_id in section_manager.list_drafts():
            console.print(f"  - {draft_id}")
        raise typer.Exit(1)

    console.print(f"\n[bold]Revising: {draft.metadata.get('section_title', section)}[/bold]")
    console.print(f"[dim]Current version: {draft.version} • {draft.word_count} words[/dim]\n")

    # Get feedback
    if interactive and not feedback:
        console.print("[cyan]Current draft preview:[/cyan]")
        preview = draft.content[:500]
        if len(draft.content) > 500:
            preview += "\n\n[... content truncated ...]"
        console.print(Panel(Markdown(preview), border_style="dim"))
        console.print()

        feedback = Prompt.ask("What would you like to improve in this section?")

    if not feedback:
        console.print("[yellow]No feedback provided. Use --feedback or --interactive[/yellow]")
        return

    if not use_ai:
        console.print("[yellow]AI disabled. Cannot revise without AI.[/yellow]")
        return

    # Perform revision
    try:
        from ..ai.claude_client import ClaudeClient
        from ..ai.prompts import PromptLibrary
        from ..core.config import config

        console.print("[dim]Initializing AI...[/dim]")
        claude_client = ClaudeClient()
        citation_manager = CitationManager(style=config.get_citation_style())
        section_manager.claude_client = claude_client
        section_manager.citation_manager = citation_manager

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"Revising section (v{draft.version + 1})...", total=None)

            # Generate revision prompt
            system_prompt, user_prompt = PromptLibrary.section_revision(
                original_content=draft.content,
                feedback=feedback,
                iteration=draft.version + 1
            )

            # Get revised content
            revised_content = claude_client.generate(
                prompt=user_prompt,
                system=system_prompt,
                max_tokens=8000,
                temperature=0.7
            )

            # Update draft
            new_draft = section_manager.update_draft(
                section_id=section,
                new_content=revised_content,
                increment_version=True
            )

            # Save citations
            citations_file = project.get_research_dir() / "citations.json"
            citation_manager.save(citations_file)

            progress.update(task, completed=True)

        console.print(f"\n[green]✓[/green] Revised {draft.metadata.get('section_title', section)}")
        console.print(f"[dim]Version:[/dim] {draft.version} → {new_draft.version}")
        console.print(f"[dim]Word count:[/dim] {draft.word_count} → {new_draft.word_count}")
        console.print(f"[dim]Citations:[/dim] {len(draft.citation_keys)} → {len(new_draft.citation_keys)}")

        # Show what changed
        if interactive:
            if Confirm.ask("\nView revised content?", default=True):
                console.print(f"\n[bold cyan]Revised Content:[/bold cyan]\n")
                console.print(Markdown(revised_content))

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)


@app.command("all")
def revise_all(
    feedback: str = typer.Option(..., help="Feedback to apply to all sections"),
    skip_sections: Optional[str] = typer.Option(None, help="Comma-separated section IDs to skip"),
    use_ai: bool = typer.Option(True, help="Use AI for revision"),
):
    """Revise all drafted sections with the same feedback."""
    project = _get_project()

    if not use_ai:
        console.print("[yellow]AI disabled. Cannot revise without AI.[/yellow]")
        return

    section_manager = SectionManager(project.root_path)
    drafts = section_manager.list_drafts()

    if not drafts:
        console.print("[yellow]No drafts found to revise.[/yellow]")
        return

    # Filter sections to skip
    skip_list = []
    if skip_sections:
        skip_list = [s.strip() for s in skip_sections.split(',')]

    sections_to_revise = [s for s in drafts if s not in skip_list]

    if not sections_to_revise:
        console.print("[yellow]All sections skipped.[/yellow]")
        return

    console.print(f"\n[bold]Revising {len(sections_to_revise)} sections...[/bold]")
    console.print(f"[dim]Feedback: {feedback}[/dim]\n")

    try:
        from ..ai.claude_client import ClaudeClient
        from ..ai.prompts import PromptLibrary
        from ..core.config import config

        claude_client = ClaudeClient()
        citation_manager = CitationManager(style=config.get_citation_style())
        section_manager.claude_client = claude_client
        section_manager.citation_manager = citation_manager

        for i, section_id in enumerate(sections_to_revise, 1):
            draft = section_manager.load_draft(section_id)
            if not draft:
                continue

            console.print(f"[cyan]({i}/{len(sections_to_revise)})[/cyan] {draft.metadata.get('section_title', section_id)}")

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Revising...", total=None)

                # Generate revision
                system_prompt, user_prompt = PromptLibrary.section_revision(
                    original_content=draft.content,
                    feedback=feedback,
                    iteration=draft.version + 1
                )

                revised_content = claude_client.generate(
                    prompt=user_prompt,
                    system=system_prompt,
                    max_tokens=8000,
                    temperature=0.7
                )

                # Update draft
                new_draft = section_manager.update_draft(
                    section_id=section_id,
                    new_content=revised_content,
                    increment_version=True
                )

                progress.update(task, completed=True)

            console.print(f"  [green]✓[/green] v{draft.version} → v{new_draft.version}, {new_draft.word_count} words\n")

        # Save citations
        citations_file = project.get_research_dir() / "citations.json"
        citation_manager.save(citations_file)

        console.print(f"[green]✓[/green] All sections revised!")

        # Mark stage as completed
        state = project.state
        state.mark_stage_completed("revise")
        project.save_state()

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)


@app.command("compare")
def compare_versions(
    section: str = typer.Argument(..., help="Section ID to compare"),
    version1: int = typer.Option(None, help="First version number (default: previous)"),
    version2: int = typer.Option(None, help="Second version number (default: current)"),
):
    """Compare different versions of a section."""
    project = _get_project()

    section_manager = SectionManager(project.root_path)

    # Get current draft
    current_draft = section_manager.load_draft(section)
    if not current_draft:
        console.print(f"[red]Error: No draft found for section '{section}'.[/red]")
        raise typer.Exit(1)

    # Get version history
    versions = section_manager.get_version_history(section)
    if not versions:
        console.print(f"[yellow]No version history found for section '{section}'.[/yellow]")
        return

    # Determine versions to compare
    if version2 is None:
        version2 = current_draft.version

    if version1 is None:
        # Compare with previous version
        if version2 > 1:
            version1 = version2 - 1
        else:
            console.print("[yellow]Only one version exists.[/yellow]")
            return

    # Load versions
    version1_file = section_manager.versions_dir / f"{section}_v{version1}.md"
    version2_file = section_manager.versions_dir / f"{section}_v{version2}.md"

    if not version1_file.exists():
        console.print(f"[red]Version {version1} not found.[/red]")
        return

    if version2 == current_draft.version:
        content2 = current_draft.content
    elif version2_file.exists():
        with open(version2_file, 'r') as f:
            content2 = f.read()
    else:
        console.print(f"[red]Version {version2} not found.[/red]")
        return

    with open(version1_file, 'r') as f:
        content1 = f.read()

    # Display comparison
    console.print(f"\n[bold]Comparing {section}:[/bold]")
    console.print(f"[dim]Version {version1} vs Version {version2}[/dim]\n")

    # Word count comparison
    words1 = len(content1.split())
    words2 = len(content2.split())
    word_diff = words2 - words1

    console.print(f"[cyan]Word Count:[/cyan]")
    console.print(f"  v{version1}: {words1} words")
    console.print(f"  v{version2}: {words2} words")
    if word_diff > 0:
        console.print(f"  [green]+{word_diff} words[/green]")
    elif word_diff < 0:
        console.print(f"  [red]{word_diff} words[/red]")
    else:
        console.print(f"  [dim]No change[/dim]")

    # Show both versions side by side (simplified)
    console.print(f"\n[bold cyan]Version {version1}:[/bold cyan]")
    preview1 = content1[:400]
    if len(content1) > 400:
        preview1 += "\n[... truncated ...]"
    console.print(Panel(Markdown(preview1), border_style="blue"))

    console.print(f"\n[bold cyan]Version {version2}:[/bold cyan]")
    preview2 = content2[:400]
    if len(content2) > 400:
        preview2 += "\n[... truncated ...]"
    console.print(Panel(Markdown(preview2), border_style="green"))


@app.command("revert")
def revert_version(
    section: str = typer.Argument(..., help="Section ID to revert"),
    version: int = typer.Argument(..., help="Version number to revert to"),
):
    """Revert a section to a previous version."""
    project = _get_project()

    section_manager = SectionManager(project.root_path)

    # Check if section exists
    current_draft = section_manager.load_draft(section)
    if not current_draft:
        console.print(f"[red]Error: No draft found for section '{section}'.[/red]")
        raise typer.Exit(1)

    # Load version to revert to
    version_file = section_manager.versions_dir / f"{section}_v{version}.md"
    if not version_file.exists():
        console.print(f"[red]Version {version} not found.[/red]")
        available = section_manager.get_version_history(section)
        if available:
            console.print(f"\n[dim]Available versions: {', '.join(map(str, available))}[/dim]")
        raise typer.Exit(1)

    with open(version_file, 'r') as f:
        old_content = f.read()

    # Confirm revert
    console.print(f"\n[yellow]This will revert {section} from v{current_draft.version} to v{version}.[/yellow]")
    if not Confirm.ask("Continue?", default=False):
        console.print("Cancelled.")
        return

    # Update draft with old content (as new version)
    new_draft = section_manager.update_draft(
        section_id=section,
        new_content=old_content,
        increment_version=True
    )

    console.print(f"\n[green]✓[/green] Reverted {section} to version {version} content")
    console.print(f"[dim]Saved as new version {new_draft.version}[/dim]")


@app.command("history")
def show_history(
    section: str = typer.Argument(..., help="Section ID"),
):
    """Show version history for a section."""
    project = _get_project()

    section_manager = SectionManager(project.root_path)

    current_draft = section_manager.load_draft(section)
    if not current_draft:
        console.print(f"[red]Error: No draft found for section '{section}'.[/red]")
        raise typer.Exit(1)

    versions = section_manager.get_version_history(section)
    if not versions:
        console.print(f"[yellow]No version history found.[/yellow]")
        return

    console.print(f"\n[bold]Version History: {section}[/bold]\n")

    for v in sorted(versions):
        version_file = section_manager.versions_dir / f"{section}_v{v}.md"
        if version_file.exists():
            with open(version_file, 'r') as f:
                content = f.read()
            words = len(content.split())

            current_marker = " [cyan](current)[/cyan]" if v == current_draft.version else ""
            console.print(f"[bold]Version {v}{current_marker}[/bold]")
            console.print(f"  Words: {words}")

            # Try to get metadata if available
            if v == current_draft.version:
                console.print(f"  Citations: {len(current_draft.citation_keys)}")
                console.print(f"  Updated: {current_draft.updated_at.strftime('%Y-%m-%d %H:%M')}")

            console.print()


@app.command("polish")
def polish_section(
    section: str = typer.Argument(..., help="Section ID to polish"),
    focus: Optional[str] = typer.Option(
        None,
        help="Focus area (clarity, flow, citations, conciseness)"
    ),
    use_ai: bool = typer.Option(True, help="Use AI for polishing"),
):
    """Polish a section to improve quality (focused refinement)."""
    project = _get_project()

    section_manager = SectionManager(project.root_path)
    draft = section_manager.load_draft(section)

    if not draft:
        console.print(f"[red]Error: No draft found for section '{section}'.[/red]")
        raise typer.Exit(1)

    if not use_ai:
        console.print("[yellow]AI disabled. Cannot polish without AI.[/yellow]")
        return

    # Determine feedback based on focus
    focus_feedback = {
        "clarity": "Improve clarity and readability. Simplify complex sentences and ensure ideas are clearly expressed.",
        "flow": "Improve the logical flow and transitions between paragraphs. Ensure smooth progression of ideas.",
        "citations": "Strengthen the use of citations. Add citations where claims need support and ensure proper attribution.",
        "conciseness": "Make the writing more concise. Remove redundant phrases and tighten the prose without losing meaning.",
    }

    if focus and focus in focus_feedback:
        feedback = focus_feedback[focus]
        console.print(f"[dim]Focus: {focus}[/dim]")
    else:
        feedback = "Polish this section to improve overall quality, clarity, and academic rigor."

    try:
        from ..ai.claude_client import ClaudeClient
        from ..ai.prompts import PromptLibrary
        from ..core.config import config

        console.print("[dim]Initializing AI...[/dim]")
        claude_client = ClaudeClient()
        citation_manager = CitationManager(style=config.get_citation_style())
        section_manager.claude_client = claude_client
        section_manager.citation_manager = citation_manager

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"Polishing {section}...", total=None)

            system_prompt, user_prompt = PromptLibrary.section_revision(
                original_content=draft.content,
                feedback=feedback,
                iteration=draft.version + 1
            )

            polished_content = claude_client.generate(
                prompt=user_prompt,
                system=system_prompt,
                max_tokens=8000,
                temperature=0.7
            )

            new_draft = section_manager.update_draft(
                section_id=section,
                new_content=polished_content,
                increment_version=True
            )

            citations_file = project.get_research_dir() / "citations.json"
            citation_manager.save(citations_file)

            progress.update(task, completed=True)

        console.print(f"\n[green]✓[/green] Polished {draft.metadata.get('section_title', section)}")
        console.print(f"[dim]Version:[/dim] {draft.version} → {new_draft.version}")

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
