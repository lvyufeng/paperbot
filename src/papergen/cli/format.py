"""Format CLI commands."""

from pathlib import Path
from typing import Optional
import subprocess

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

from ..core.project import PaperProject
from ..document.outline import Outline
from ..document.section import SectionManager
from ..document.citation import CitationManager
from ..templates.latex_builder import LaTeXBuilder
from ..templates.markdown_builder import MarkdownBuilder

app = typer.Typer(name="format", help="Format and compile paper")
console = Console()


def _get_project() -> PaperProject:
    """Get current project or exit."""
    from ..cli.main import _get_project as get_proj
    return get_proj()


@app.command("latex")
def format_latex(
    template: Optional[str] = typer.Option(None, help="Template name (ieee, acm, springer)"),
    output: Optional[Path] = typer.Option(None, help="Output file path"),
):
    """Generate LaTeX document from drafts."""
    project = _get_project()
    state = project.state

    # Use project template if not specified
    if not template:
        template = state.template

    console.print(f"\n[bold]Generating LaTeX document...[/bold]")
    console.print(f"[dim]Template: {template}[/dim]\n")

    # Load outline
    outline_file = project.get_outline_dir() / "outline.json"
    if not outline_file.exists():
        console.print("[yellow]Warning: No outline found. Proceeding anyway...[/yellow]")
        outline = None
    else:
        outline = Outline.from_json_file(outline_file)

    # Load all drafts
    section_manager = SectionManager(project.root_path)
    drafts = section_manager.list_drafts()

    if not drafts:
        console.print("[red]Error: No drafts found. Draft sections first with 'papergen draft'.[/red]")
        raise typer.Exit(1)

    console.print(f"[dim]Loading {len(drafts)} sections...[/dim]")

    # Load section content
    sections_content = {}
    for section_id in drafts:
        content = section_manager.get_draft_content(section_id)
        if content:
            sections_content[section_id] = content

    # Load citations
    citations_file = project.get_research_dir() / "citations.json"
    if citations_file.exists():
        citation_manager = CitationManager.load(citations_file)
    else:
        from ..core.config import config
        citation_manager = CitationManager(style=config.get_citation_style())

    # Prepare metadata
    metadata = {
        'title': state.metadata.title or state.topic,
        'authors': state.metadata.authors or ['Anonymous'],
        'keywords': state.metadata.keywords or [],
        'date': r'\today',
    }

    # Build LaTeX document
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Generating LaTeX...", total=None)

        builder = LaTeXBuilder(template=template)
        latex_content = builder.build(
            sections=sections_content,
            metadata=metadata,
            citation_manager=citation_manager
        )

        progress.update(task, completed=True)

    # Save to file
    if output:
        output_path = Path(output)
    else:
        output_path = project.get_output_dir() / "paper.tex"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(latex_content)

    # Also save BibTeX if there are citations
    if citation_manager.citations:
        bib_path = output_path.parent / f"{output_path.stem}.bib"
        with open(bib_path, 'w') as f:
            f.write(citation_manager.export_bibtex())
        console.print(f"[green]✓[/green] Bibliography saved to {bib_path}")

    console.print(f"[green]✓[/green] LaTeX document saved to {output_path}")
    console.print(f"\n[dim]File size:[/dim] {len(latex_content)} characters")
    console.print(f"[dim]Sections:[/dim] {len(sections_content)}")
    console.print(f"[dim]Citations:[/dim] {len(citation_manager.citations)}")

    console.print(f"\n[cyan]Next step:[/cyan] papergen format compile")


@app.command("markdown")
def format_markdown(
    template: Optional[str] = typer.Option("standard", help="Template (standard, arxiv, github)"),
    output: Optional[Path] = typer.Option(None, help="Output file path"),
    toc: bool = typer.Option(True, help="Include table of contents"),
):
    """Generate Markdown document from drafts."""
    project = _get_project()
    state = project.state

    console.print(f"\n[bold]Generating Markdown document...[/bold]")
    console.print(f"[dim]Template: {template}[/dim]\n")

    # Load all drafts
    section_manager = SectionManager(project.root_path)
    drafts = section_manager.list_drafts()

    if not drafts:
        console.print("[red]Error: No drafts found. Draft sections first.[/red]")
        raise typer.Exit(1)

    # Load section content
    sections_content = {}
    for section_id in drafts:
        content = section_manager.get_draft_content(section_id)
        if content:
            sections_content[section_id] = content

    # Load citations
    citations_file = project.get_research_dir() / "citations.json"
    if citations_file.exists():
        citation_manager = CitationManager.load(citations_file)
    else:
        from ..core.config import config
        citation_manager = CitationManager(style=config.get_citation_style())

    # Prepare metadata
    metadata = {
        'title': state.metadata.title or state.topic,
        'authors': state.metadata.authors or ['Anonymous'],
        'keywords': state.metadata.keywords or [],
    }

    # Build Markdown document
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Generating Markdown...", total=None)

        builder = MarkdownBuilder(template=template)
        markdown_content = builder.build(
            sections=sections_content,
            metadata=metadata,
            citation_manager=citation_manager,
            include_toc=toc
        )

        progress.update(task, completed=True)

    # Save to file
    if output:
        output_path = Path(output)
    else:
        output_path = project.get_output_dir() / "paper.md"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(markdown_content)

    console.print(f"[green]✓[/green] Markdown document saved to {output_path}")
    console.print(f"\n[dim]Word count:[/dim] {len(markdown_content.split())}")
    console.print(f"[dim]Sections:[/dim] {len(sections_content)}")
    console.print(f"[dim]Citations:[/dim] {len(citation_manager.citations)}")

    # Mark format stage as completed
    state.mark_stage_completed("format")
    project.save_state()


@app.command("compile")
def compile_latex(
    source: Optional[Path] = typer.Option(None, help="LaTeX source file"),
    open_pdf: bool = typer.Option(False, "--open", help="Open PDF after compilation"),
    engine: str = typer.Option("pdflatex", help="LaTeX engine (pdflatex, xelatex, lualatex)"),
):
    """Compile LaTeX to PDF."""
    project = _get_project()

    # Determine source file
    if source:
        tex_file = Path(source)
    else:
        tex_file = project.get_output_dir() / "paper.tex"

    if not tex_file.exists():
        console.print(f"[red]Error: LaTeX file not found: {tex_file}[/red]")
        console.print("\n[dim]Generate LaTeX first with: papergen format latex[/dim]")
        raise typer.Exit(1)

    console.print(f"\n[bold]Compiling LaTeX to PDF...[/bold]")
    console.print(f"[dim]Source: {tex_file}[/dim]")
    console.print(f"[dim]Engine: {engine}[/dim]\n")

    # Check if LaTeX is installed
    try:
        subprocess.run([engine, "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        console.print(f"[red]Error: {engine} not found. Please install a LaTeX distribution.[/red]")
        console.print("\n[dim]Install options:[/dim]")
        console.print("  • macOS: brew install --cask mactex")
        console.print("  • Ubuntu: sudo apt-get install texlive-full")
        console.print("  • Windows: Download MiKTeX from miktex.org")
        raise typer.Exit(1)

    # Compile (run twice for references)
    output_dir = tex_file.parent
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Compiling (pass 1)...", total=None)

        # First pass
        result1 = subprocess.run(
            [engine, "-interaction=nonstopmode", "-output-directory", str(output_dir), str(tex_file)],
            capture_output=True,
            text=True,
            cwd=output_dir
        )

        progress.update(task, description="Compiling (pass 2)...")

        # Second pass (for references)
        result2 = subprocess.run(
            [engine, "-interaction=nonstopmode", "-output-directory", str(output_dir), str(tex_file)],
            capture_output=True,
            text=True,
            cwd=output_dir
        )

        progress.update(task, completed=True)

    pdf_file = output_dir / f"{tex_file.stem}.pdf"

    if pdf_file.exists():
        console.print(f"\n[green]✓[/green] PDF compiled successfully!")
        console.print(f"[dim]Output:[/dim] {pdf_file}")

        # Show file size
        size_kb = pdf_file.stat().st_size / 1024
        console.print(f"[dim]Size:[/dim] {size_kb:.1f} KB")

        # Open PDF if requested
        if open_pdf:
            console.print("\n[dim]Opening PDF...[/dim]")
            import platform
            system = platform.system()

            try:
                if system == "Darwin":  # macOS
                    subprocess.run(["open", str(pdf_file)])
                elif system == "Linux":
                    subprocess.run(["xdg-open", str(pdf_file)])
                elif system == "Windows":
                    subprocess.run(["start", str(pdf_file)], shell=True)
            except Exception as e:
                console.print(f"[yellow]Could not open PDF: {e}[/yellow]")

        # Mark format stage as completed
        state = project.state
        state.mark_stage_completed("format")
        project.save_state()

    else:
        console.print(f"\n[red]✗[/red] Compilation failed!")
        console.print("\n[dim]LaTeX output:[/dim]")
        console.print(result2.stdout[-1000:] if len(result2.stdout) > 1000 else result2.stdout)

        # Save log
        log_file = output_dir / f"{tex_file.stem}.log"
        if log_file.exists():
            console.print(f"\n[dim]See full log:[/dim] {log_file}")

        raise typer.Exit(1)


@app.command("preview")
def preview_output(
    format: str = typer.Option("latex", help="Format to preview (latex, markdown)"),
    lines: int = typer.Option(50, help="Number of lines to show"),
):
    """Preview generated output without saving."""
    project = _get_project()
    state = project.state

    # Load drafts
    section_manager = SectionManager(project.root_path)
    drafts = section_manager.list_drafts()

    if not drafts:
        console.print("[yellow]No drafts found.[/yellow]")
        return

    sections_content = {}
    for section_id in drafts:
        content = section_manager.get_draft_content(section_id)
        if content:
            sections_content[section_id] = content

    # Load citations
    citations_file = project.get_research_dir() / "citations.json"
    if citations_file.exists():
        citation_manager = CitationManager.load(citations_file)
    else:
        from ..core.config import config
        citation_manager = CitationManager(style=config.get_citation_style())

    metadata = {
        'title': state.metadata.title or state.topic,
        'authors': state.metadata.authors or ['Anonymous'],
        'keywords': state.metadata.keywords or [],
    }

    # Generate preview
    if format == "latex":
        builder = LaTeXBuilder(template=state.template)
        content = builder.build(sections_content, metadata, citation_manager)
    else:
        builder = MarkdownBuilder()
        content = builder.build(sections_content, metadata, citation_manager)

    # Show preview
    preview_lines = content.split('\n')[:lines]
    console.print(f"\n[bold cyan]Preview ({format.upper()}):[/bold cyan]\n")
    console.print(Panel('\n'.join(preview_lines), border_style="dim"))

    if len(content.split('\n')) > lines:
        console.print(f"\n[dim]... and {len(content.split('\n')) - lines} more lines[/dim]")


@app.command("stats")
def show_stats():
    """Show document statistics."""
    project = _get_project()

    section_manager = SectionManager(project.root_path)
    stats = section_manager.get_statistics()

    console.print("\n[bold]Document Statistics:[/bold]\n")
    console.print(f"  Sections: {stats['sections_drafted']}")
    console.print(f"  Total words: {stats['total_words']}")
    console.print(f"  Citations: {stats['total_citations']}")
    console.print(f"  Average words/section: {stats['average_words_per_section']}")

    # Check if formatted
    latex_file = project.get_output_dir() / "paper.tex"
    pdf_file = project.get_output_dir() / "paper.pdf"
    md_file = project.get_output_dir() / "paper.md"

    console.print("\n[bold]Output Files:[/bold]")
    if latex_file.exists():
        console.print(f"  [green]✓[/green] LaTeX: {latex_file}")
    if pdf_file.exists():
        size_kb = pdf_file.stat().st_size / 1024
        console.print(f"  [green]✓[/green] PDF: {pdf_file} ({size_kb:.1f} KB)")
    if md_file.exists():
        console.print(f"  [green]✓[/green] Markdown: {md_file}")

    if not any([latex_file.exists(), pdf_file.exists(), md_file.exists()]):
        console.print("  [dim]No output files yet[/dim]")


if __name__ == "__main__":
    app()
