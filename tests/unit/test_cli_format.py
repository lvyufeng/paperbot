"""Tests for format CLI commands."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import subprocess

from typer.testing import CliRunner

from papergen.cli.format import app


runner = CliRunner()


class TestFormatLatexCommand:
    """Tests for format latex command."""

    @pytest.fixture
    def mock_project(self):
        """Create mock project."""
        project = Mock()
        project.root_path = Path("/tmp/test")
        project.state = Mock()
        project.state.template = "ieee"
        project.state.metadata = Mock()
        project.state.metadata.title = "Test Paper"
        project.state.metadata.authors = ["Author One"]
        project.state.metadata.keywords = ["ai"]
        project.state.topic = "Test Topic"
        project.get_outline_dir.return_value = Path("/tmp/test/outline")
        project.get_research_dir.return_value = Path("/tmp/test/research")
        project.get_output_dir.return_value = Path("/tmp/test/output")
        return project

    def test_format_latex_no_drafts(self, mock_project):
        """Test format latex when no drafts exist."""
        mock_manager = Mock()
        mock_manager.list_drafts.return_value = []

        with patch('papergen.cli.format._get_project', return_value=mock_project):
            with patch('papergen.cli.format.SectionManager', return_value=mock_manager):
                with tempfile.TemporaryDirectory() as tmpdir:
                    mock_project.get_outline_dir.return_value = Path(tmpdir)
                    mock_project.get_output_dir.return_value = Path(tmpdir)

                    result = runner.invoke(app, ["latex"])
                    assert result.exit_code != 0
                    assert "no drafts" in result.output.lower()

    def test_format_latex_success(self, mock_project):
        """Test successful LaTeX generation."""
        mock_manager = Mock()
        mock_manager.list_drafts.return_value = ['intro', 'methods']
        mock_manager.get_draft_content.return_value = "Test content"

        mock_citation_manager = Mock()
        mock_citation_manager.citations = {}

        mock_builder = Mock()
        mock_builder.build.return_value = "\\documentclass{article}\\begin{document}Test\\end{document}"

        with patch('papergen.cli.format._get_project', return_value=mock_project):
            with patch('papergen.cli.format.SectionManager', return_value=mock_manager):
                with patch('papergen.cli.format.LaTeXBuilder', return_value=mock_builder):
                    with patch('papergen.cli.format.CitationManager') as mock_cm_class:
                        mock_cm_class.return_value = mock_citation_manager
                        mock_cm_class.load.return_value = mock_citation_manager

                        with tempfile.TemporaryDirectory() as tmpdir:
                            mock_project.get_output_dir.return_value = Path(tmpdir)
                            mock_project.get_research_dir.return_value = Path(tmpdir)

                            result = runner.invoke(app, ["latex"])
                            assert result.exit_code == 0
                            assert "saved" in result.output.lower()


class TestFormatMarkdownCommand:
    """Tests for format markdown command."""

    @pytest.fixture
    def mock_project(self):
        """Create mock project."""
        project = Mock()
        project.root_path = Path("/tmp/test")
        project.state = Mock()
        project.state.template = "standard"
        project.state.metadata = Mock()
        project.state.metadata.title = "Test Paper"
        project.state.metadata.authors = ["Author"]
        project.state.metadata.keywords = []
        project.state.topic = "Topic"
        project.get_research_dir.return_value = Path("/tmp/test/research")
        project.get_output_dir.return_value = Path("/tmp/test/output")
        project.save_state = Mock()
        return project

    def test_format_markdown_no_drafts(self, mock_project):
        """Test markdown format when no drafts exist."""
        mock_manager = Mock()
        mock_manager.list_drafts.return_value = []

        with patch('papergen.cli.format._get_project', return_value=mock_project):
            with patch('papergen.cli.format.SectionManager', return_value=mock_manager):
                result = runner.invoke(app, ["markdown"])
                assert result.exit_code != 0

    def test_format_markdown_success(self, mock_project):
        """Test successful markdown generation."""
        mock_manager = Mock()
        mock_manager.list_drafts.return_value = ['intro']
        mock_manager.get_draft_content.return_value = "Content"

        mock_citation_manager = Mock()
        mock_citation_manager.citations = {}

        mock_builder = Mock()
        mock_builder.build.return_value = "# Test Paper\n\nContent"

        with patch('papergen.cli.format._get_project', return_value=mock_project):
            with patch('papergen.cli.format.SectionManager', return_value=mock_manager):
                with patch('papergen.cli.format.MarkdownBuilder', return_value=mock_builder):
                    with patch('papergen.cli.format.CitationManager') as mock_cm_class:
                        mock_cm_class.return_value = mock_citation_manager
                        mock_cm_class.load.return_value = mock_citation_manager

                        with tempfile.TemporaryDirectory() as tmpdir:
                            mock_project.get_output_dir.return_value = Path(tmpdir)
                            mock_project.get_research_dir.return_value = Path(tmpdir)

                            result = runner.invoke(app, ["markdown"])
                            assert result.exit_code == 0

    def test_format_markdown_without_toc(self, mock_project):
        """Test markdown without table of contents."""
        mock_manager = Mock()
        mock_manager.list_drafts.return_value = ['intro']
        mock_manager.get_draft_content.return_value = "Content"

        mock_citation_manager = Mock()
        mock_citation_manager.citations = {}

        mock_builder = Mock()
        mock_builder.build.return_value = "# Test\n\nContent"

        with patch('papergen.cli.format._get_project', return_value=mock_project):
            with patch('papergen.cli.format.SectionManager', return_value=mock_manager):
                with patch('papergen.cli.format.MarkdownBuilder', return_value=mock_builder):
                    with patch('papergen.cli.format.CitationManager') as mock_cm_class:
                        mock_cm_class.return_value = mock_citation_manager

                        with tempfile.TemporaryDirectory() as tmpdir:
                            mock_project.get_output_dir.return_value = Path(tmpdir)
                            mock_project.get_research_dir.return_value = Path(tmpdir)

                            result = runner.invoke(app, ["markdown", "--no-toc"])
                            assert result.exit_code == 0


class TestCompileLatexCommand:
    """Tests for compile command."""

    @pytest.fixture
    def mock_project(self):
        """Create mock project."""
        project = Mock()
        project.root_path = Path("/tmp/test")
        project.state = Mock()
        project.get_output_dir.return_value = Path("/tmp/test/output")
        project.save_state = Mock()
        return project

    def test_compile_no_source(self, mock_project):
        """Test compile when no source exists."""
        with patch('papergen.cli.format._get_project', return_value=mock_project):
            with tempfile.TemporaryDirectory() as tmpdir:
                mock_project.get_output_dir.return_value = Path(tmpdir)
                result = runner.invoke(app, ["compile"])
                assert result.exit_code != 0
                assert "not found" in result.output.lower()

    def test_compile_no_latex_installed(self, mock_project):
        """Test compile when LaTeX not installed."""
        with patch('papergen.cli.format._get_project', return_value=mock_project):
            with patch('subprocess.run') as mock_run:
                mock_run.side_effect = FileNotFoundError()

                with tempfile.TemporaryDirectory() as tmpdir:
                    tex_file = Path(tmpdir) / "paper.tex"
                    tex_file.write_text("\\documentclass{article}")
                    mock_project.get_output_dir.return_value = Path(tmpdir)

                    result = runner.invoke(app, ["compile"])
                    assert result.exit_code != 0
                    assert "not found" in result.output.lower()


class TestPreviewCommand:
    """Tests for preview command."""

    @pytest.fixture
    def mock_project(self):
        """Create mock project."""
        project = Mock()
        project.root_path = Path("/tmp/test")
        project.state = Mock()
        project.state.template = "ieee"
        project.state.metadata = Mock()
        project.state.metadata.title = "Test"
        project.state.metadata.authors = []
        project.state.metadata.keywords = []
        project.state.topic = "Topic"
        project.get_research_dir.return_value = Path("/tmp/test/research")
        return project

    def test_preview_no_drafts(self, mock_project):
        """Test preview when no drafts exist."""
        mock_manager = Mock()
        mock_manager.list_drafts.return_value = []

        with patch('papergen.cli.format._get_project', return_value=mock_project):
            with patch('papergen.cli.format.SectionManager', return_value=mock_manager):
                result = runner.invoke(app, ["preview"])
                assert "no drafts" in result.output.lower()

    def test_preview_latex(self, mock_project):
        """Test preview in latex format."""
        mock_manager = Mock()
        mock_manager.list_drafts.return_value = ['intro']
        mock_manager.get_draft_content.return_value = "Content"

        mock_citation_manager = Mock()
        mock_citation_manager.citations = {}

        mock_builder = Mock()
        mock_builder.build.return_value = "\\documentclass{article}\n" * 100

        with patch('papergen.cli.format._get_project', return_value=mock_project):
            with patch('papergen.cli.format.SectionManager', return_value=mock_manager):
                with patch('papergen.cli.format.LaTeXBuilder', return_value=mock_builder):
                    with patch('papergen.cli.format.CitationManager') as mock_cm:
                        mock_cm.return_value = mock_citation_manager
                        mock_cm.load.return_value = mock_citation_manager

                        with tempfile.TemporaryDirectory() as tmpdir:
                            mock_project.get_research_dir.return_value = Path(tmpdir)

                            result = runner.invoke(app, ["preview", "--format", "latex"])
                            assert result.exit_code == 0


class TestStatsCommand:
    """Tests for stats command."""

    def test_stats_command(self):
        """Test stats command."""
        mock_project = Mock()
        mock_project.root_path = Path("/tmp/test")

        mock_manager = Mock()
        mock_manager.get_statistics.return_value = {
            'sections_drafted': 5,
            'total_words': 5000,
            'total_citations': 20,
            'average_words_per_section': 1000
        }

        with patch('papergen.cli.format._get_project', return_value=mock_project):
            with patch('papergen.cli.format.SectionManager', return_value=mock_manager):
                with tempfile.TemporaryDirectory() as tmpdir:
                    mock_project.get_output_dir.return_value = Path(tmpdir)

                    result = runner.invoke(app, ["stats"])
                    assert result.exit_code == 0
                    assert "5000" in result.output

    def test_stats_with_output_files(self):
        """Test stats when output files exist."""
        mock_project = Mock()
        mock_project.root_path = Path("/tmp/test")

        mock_manager = Mock()
        mock_manager.get_statistics.return_value = {
            'sections_drafted': 1,
            'total_words': 100,
            'total_citations': 1,
            'average_words_per_section': 100
        }

        with patch('papergen.cli.format._get_project', return_value=mock_project):
            with patch('papergen.cli.format.SectionManager', return_value=mock_manager):
                with tempfile.TemporaryDirectory() as tmpdir:
                    # Create output files
                    (Path(tmpdir) / "paper.tex").write_text("test")
                    (Path(tmpdir) / "paper.md").write_text("test")
                    mock_project.get_output_dir.return_value = Path(tmpdir)

                    result = runner.invoke(app, ["stats"])
                    assert result.exit_code == 0
                    assert "latex" in result.output.lower() or "paper.tex" in result.output
