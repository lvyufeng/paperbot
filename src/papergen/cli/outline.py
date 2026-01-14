"""Outline CLI commands."""

from pathlib import Path
from typing import Optional, List

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.panel import Panel

from ..core.project import PaperProject
from ..core.config import config
from ..document.outline import Outline, OutlineGenerator

app = typer.Typer(name="outline", help="Generate and refine paper outline")
console = Console()


def _get_project() -> PaperProject:
    """Get current project or exit."""
    from ..cli.main import _get_project as get_proj
    return get_proj()


@app.command("generate")
def generate_outline(
    sections: Optional[str] = typer.Option(
        None,
        help="Comma-separated section names (e.g., 'intro,methods,results,discussion,conclusion')"
    ),
    use_ai: bool = typer.Option(True, help="Use AI for generation (requires API key)"),
):
    """Generate paper outline from organized research."""
    project = _get_project()
    state = project.state

    # Check if research is complete
    if state.get_stage_status("research").value != "completed":
        console.print("[yellow]Warning: Research stage not completed. Run 'papergen research organize' first.[/yellow]")
        if not Confirm.ask("Continue anyway?"):
            return

    # Load organized research
    research_file = project.get_research_dir() / "organized_notes.md"
    if not research_file.exists():
        console.print("[red]Error: No organized research found. Run 'papergen research organize' first.[/red]")
        raise typer.Exit(1)

    with open(research_file, 'r') as f:
        research_text = f.read()

    # Determine sections
    if sections:
        section_list = [s.strip() for s in sections.split(',')]
    else:
        # Default sections
        section_list = ["abstract", "introduction", "methods", "results", "discussion", "conclusion"]
        console.print(f"[dim]Using default sections: {', '.join(section_list)}[/dim]")

    # Get word count targets from config
    word_count_targets = config.get_word_count_targets()

    # Filter to requested sections
    filtered_targets = {s: word_count_targets.get(s, 1000) for s in section_list}

    if not use_ai:
        console.print("[yellow]AI disabled. Creating basic outline...[/yellow]")
        _create_basic_outline(project, state.topic, section_list, filtered_targets)
        return

    # Generate outline with AI
    try:
        from ..ai.claude_client import ClaudeClient

        console.print("[dim]Initializing AI...[/dim]")
        claude_client = ClaudeClient()
        generator = OutlineGenerator(claude_client)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Generating outline with AI...", total=None)

            outline = generator.generate(
                topic=state.topic,
                research_text=research_text,
                sections=section_list,
                word_count_targets=filtered_targets
            )

            progress.update(task, completed=True)

        # Validate outline
        if not outline.validate_structure():
            console.print("[yellow]Warning: Generated outline has validation issues. Using anyway.[/yellow]")

        # Save outline
        outline_dir = project.get_outline_dir()
        outline_json = outline_dir / "outline.json"
        outline_md = outline_dir / "outline.md"

        outline.to_json_file(outline_json)

        with open(outline_md, 'w') as f:
            f.write(outline.to_markdown())

        console.print(f"[green]✓[/green] Outline generated successfully!")
        console.print(f"[dim]Saved to:[/dim]")
        console.print(f"  - {outline_json}")
        console.print(f"  - {outline_md}")

        # Show preview
        _show_outline_preview(outline)

        # Mark stage as completed
        state.mark_stage_completed("outline")
        project.save_state()

    except Exception as e:
        console.print(f"[red]Error generating outline: {str(e)}[/red]")
        console.print("[yellow]Falling back to basic outline...[/yellow]")
        _create_basic_outline(project, state.topic, section_list, filtered_targets)


def _create_basic_outline(
    project: PaperProject,
    topic: str,
    sections: List[str],
    word_counts: dict
):
    """Create a basic outline without AI."""
    from ..document.outline import Outline, Section

    section_objects = []
    for i, section_name in enumerate(sections):
        section_objects.append(Section(
            id=section_name.lower().replace(' ', '_'),
            title=section_name.title(),
            level=0 if section_name.lower() == 'abstract' else 1,
            order=i,
            objectives=[f"Complete the {section_name} section"],
            key_points=["Point 1", "Point 2", "Point 3"],
            word_count_target=word_counts.get(section_name, 1000),
            sources=[],
            subsections=[]
        ))

    outline = Outline(
        topic=topic,
        sections=section_objects,
        metadata={"generated_with": "basic"}
    )

    # Save outline
    outline_dir = project.get_outline_dir()
    outline_json = outline_dir / "outline.json"
    outline_md = outline_dir / "outline.md"

    outline.to_json_file(outline_json)

    with open(outline_md, 'w') as f:
        f.write(outline.to_markdown())

    console.print(f"[green]✓[/green] Basic outline created.")
    console.print(f"[dim]Edit {outline_md} to customize the outline.[/dim]")

    # Mark stage as completed
    state = project.state
    state.mark_stage_completed("outline")
    project.save_state()


def _show_outline_preview(outline: Outline):
    """Show a preview of the generated outline."""
    console.print(f"\n[bold cyan]Outline Preview:[/bold cyan]")

    for section in outline.sections:
        console.print(f"\n[bold]{section.title}[/bold] ({section.word_count_target} words)")

        if section.objectives:
            console.print("[dim]Objectives:[/dim]")
            for obj in section.objectives[:2]:  # Show first 2
                console.print(f"  • {obj}")

        if section.key_points:
            console.print("[dim]Key points:[/dim]")
            for point in section.key_points[:3]:  # Show first 3
                console.print(f"  • {point}")

        if section.subsections:
            console.print(f"[dim]  + {len(section.subsections)} subsections[/dim]")


@app.command("show")
def show_outline():
    """Show the current outline."""
    project = _get_project()

    outline_file = project.get_outline_dir() / "outline.json"
    if not outline_file.exists():
        console.print("[yellow]No outline found. Generate one with 'papergen outline generate'[/yellow]")
        return

    outline = Outline.from_json_file(outline_file)

    console.print(f"\n[bold]Paper Outline: {outline.topic}[/bold]\n")

    for section in outline.sections:
        # Section header with word count
        header = f"[cyan]{section.title}[/cyan] ({section.word_count_target} words)"
        console.print(header)

        # Objectives
        if section.objectives:
            console.print("  [dim]Objectives:[/dim]")
            for obj in section.objectives:
                console.print(f"    • {obj}")

        # Key points
        if section.key_points:
            console.print("  [dim]Key Points:[/dim]")
            for point in section.key_points:
                console.print(f"    • {point}")

        # Guidance
        if section.guidance:
            console.print(f"  [dim]Note: {section.guidance}[/dim]")

        # Subsections
        if section.subsections:
            for subsection in section.subsections:
                console.print(f"    [blue]{subsection.title}[/blue] ({subsection.word_count_target} words)")

        console.print()


@app.command("refine")
def refine_outline(
    section: Optional[str] = typer.Option(None, help="Section ID to refine (refines all if not specified)"),
    interactive: bool = typer.Option(True, help="Interactive refinement mode"),
):
    """Refine the outline based on feedback."""
    project = _get_project()

    outline_file = project.get_outline_dir() / "outline.json"
    if not outline_file.exists():
        console.print("[yellow]No outline found. Generate one first with 'papergen outline generate'[/yellow]")
        return

    outline = Outline.from_json_file(outline_file)

    # Load research for context
    research_file = project.get_research_dir() / "organized_notes.md"
    research_text = ""
    if research_file.exists():
        with open(research_file, 'r') as f:
            research_text = f.read()

    if not interactive:
        console.print("[yellow]Non-interactive mode not yet implemented. Use --interactive[/yellow]")
        return

    # Interactive refinement
    console.print("[bold]Interactive Outline Refinement[/bold]\n")
    console.print("Review each section and provide feedback for improvements.\n")

    # Initialize Claude client for refinement
    try:
        from ..ai.claude_client import ClaudeClient
        claude_client = ClaudeClient()
        generator = OutlineGenerator(claude_client)
        has_ai = True
    except Exception as e:
        console.print(f"[yellow]Warning: AI not available ({str(e)}). Manual editing only.[/yellow]")
        has_ai = False

    sections_to_refine = [outline.get_section_by_id(section)] if section else outline.sections

    for sect in sections_to_refine:
        if sect is None:
            continue

        console.print(f"\n[cyan]━━━ {sect.title} ━━━[/cyan]")
        console.print(f"Current objectives: {', '.join(sect.objectives)}")
        console.print(f"Current key points: {', '.join(sect.key_points)}")

        if Confirm.ask(f"\nRefine this section?", default=False):
            feedback = Prompt.ask("What would you like to improve?")

            if has_ai and feedback:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console
                ) as progress:
                    task = progress.add_task(f"Refining {sect.title}...", total=None)

                    refined = generator.refine_section(sect, feedback, research_text)

                    # Update section in outline
                    for i, s in enumerate(outline.sections):
                        if s.id == sect.id:
                            outline.sections[i] = refined
                            break

                    progress.update(task, completed=True)

                console.print(f"[green]✓[/green] Refined {sect.title}")
                console.print(f"New objectives: {', '.join(refined.objectives)}")
                console.print(f"New key points: {', '.join(refined.key_points)}")

    # Save refined outline
    outline.to_json_file(outline_file)
    outline_md = project.get_outline_dir() / "outline.md"
    with open(outline_md, 'w') as f:
        f.write(outline.to_markdown())

    console.print(f"\n[green]✓[/green] Outline refined and saved!")


@app.command("export")
def export_outline(
    format: str = typer.Option("markdown", help="Export format (markdown, json)")
):
    """Export the outline to a file."""
    project = _get_project()

    outline_file = project.get_outline_dir() / "outline.json"
    if not outline_file.exists():
        console.print("[yellow]No outline found.[/yellow]")
        return

    outline = Outline.from_json_file(outline_file)

    if format == "markdown":
        output = outline.to_markdown()
        console.print(output)
    elif format == "json":
        import json
        output = json.dumps(outline.model_dump(mode='json'), indent=2)
        console.print(output)
    else:
        console.print(f"[red]Unknown format: {format}[/red]")


if __name__ == "__main__":
    app()
