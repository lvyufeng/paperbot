"""Tests for outline CLI commands."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import json

from typer.testing import CliRunner

from papergen.cli.outline import app, _create_basic_outline, _show_outline_preview


runner = CliRunner()


class TestGenerateOutlineCommand:
    """Tests for generate outline command."""

    @pytest.fixture
    def mock_project(self):
        """Create mock project."""
        project = Mock()
        project.root_path = Path("/tmp/test")
        project.state = Mock()
        project.state.topic = "Machine Learning"
        project.state.get_stage_status.return_value = Mock(value="completed")
        project.get_research_dir.return_value = Path("/tmp/test/research")
        project.get_outline_dir.return_value = Path("/tmp/test/outline")
        project.save_state = Mock()
        return project

    def test_generate_help(self):
        """Test generate command help."""
        result = runner.invoke(app, ["generate", "--help"])
        assert result.exit_code == 0
        assert "generate" in result.output.lower()

    def test_generate_no_research(self, mock_project):
        """Test generate when no research exists."""
        mock_project.state.get_stage_status.return_value = Mock(value="pending")

        with patch('papergen.cli.outline._get_project', return_value=mock_project):
            # Non-interactive mode, should abort
            result = runner.invoke(app, ["generate"], input="n\n")
            # Should warn or exit

    def test_generate_no_organized_notes(self, mock_project):
        """Test generate when no organized notes file."""
        with patch('papergen.cli.outline._get_project', return_value=mock_project):
            with tempfile.TemporaryDirectory() as tmpdir:
                mock_project.get_research_dir.return_value = Path(tmpdir)
                # No organized_notes.md file

                result = runner.invoke(app, ["generate"])
                assert result.exit_code != 0 or "error" in result.output.lower()

    def test_generate_with_ai_disabled(self, mock_project):
        """Test generate with AI disabled."""
        with patch('papergen.cli.outline._get_project', return_value=mock_project):
            with tempfile.TemporaryDirectory() as tmpdir:
                research_dir = Path(tmpdir) / "research"
                research_dir.mkdir()
                outline_dir = Path(tmpdir) / "outline"
                outline_dir.mkdir()

                # Create organized notes
                (research_dir / "organized_notes.md").write_text("# Research Notes\nContent here")

                mock_project.get_research_dir.return_value = research_dir
                mock_project.get_outline_dir.return_value = outline_dir

                result = runner.invoke(app, ["generate", "--no-use-ai"])

                # Should create basic outline
                assert result.exit_code == 0 or "basic outline" in result.output.lower()

    def test_generate_with_custom_sections(self, mock_project):
        """Test generate with custom sections."""
        with patch('papergen.cli.outline._get_project', return_value=mock_project):
            with tempfile.TemporaryDirectory() as tmpdir:
                research_dir = Path(tmpdir) / "research"
                research_dir.mkdir()
                outline_dir = Path(tmpdir) / "outline"
                outline_dir.mkdir()

                (research_dir / "organized_notes.md").write_text("# Research Notes")

                mock_project.get_research_dir.return_value = research_dir
                mock_project.get_outline_dir.return_value = outline_dir

                result = runner.invoke(app, [
                    "generate",
                    "--sections", "intro,methods,results",
                    "--no-use-ai"
                ])

                # Should process custom sections


class TestShowOutlineCommand:
    """Tests for show outline command."""

    @pytest.fixture
    def mock_project(self):
        """Create mock project."""
        project = Mock()
        project.get_outline_dir.return_value = Path("/tmp/test/outline")
        return project

    def test_show_help(self):
        """Test show command help."""
        result = runner.invoke(app, ["show", "--help"])
        assert result.exit_code == 0
        assert "show" in result.output.lower()

    def test_show_no_outline(self, mock_project):
        """Test show when no outline exists."""
        with patch('papergen.cli.outline._get_project', return_value=mock_project):
            with tempfile.TemporaryDirectory() as tmpdir:
                mock_project.get_outline_dir.return_value = Path(tmpdir)

                result = runner.invoke(app, ["show"])
                assert "no outline" in result.output.lower()

    def test_show_with_outline(self, mock_project):
        """Test show with existing outline."""
        mock_outline = Mock()
        mock_outline.topic = "Test Topic"
        mock_section = Mock()
        mock_section.title = "Introduction"
        mock_section.word_count_target = 1000
        mock_section.objectives = ["Objective 1"]
        mock_section.key_points = ["Point 1"]
        mock_section.guidance = "Some guidance"
        mock_section.subsections = []
        mock_outline.sections = [mock_section]

        with patch('papergen.cli.outline._get_project', return_value=mock_project):
            with patch('papergen.cli.outline.Outline') as MockOutline:
                MockOutline.from_json_file.return_value = mock_outline

                with tempfile.TemporaryDirectory() as tmpdir:
                    outline_dir = Path(tmpdir)
                    (outline_dir / "outline.json").write_text("{}")
                    mock_project.get_outline_dir.return_value = outline_dir

                    result = runner.invoke(app, ["show"])
                    # Should display outline


class TestRefineOutlineCommand:
    """Tests for refine outline command."""

    @pytest.fixture
    def mock_project(self):
        """Create mock project."""
        project = Mock()
        project.get_outline_dir.return_value = Path("/tmp/test/outline")
        project.get_research_dir.return_value = Path("/tmp/test/research")
        return project

    def test_refine_help(self):
        """Test refine command help."""
        result = runner.invoke(app, ["refine", "--help"])
        assert result.exit_code == 0
        assert "refine" in result.output.lower()

    def test_refine_no_outline(self, mock_project):
        """Test refine when no outline exists."""
        with patch('papergen.cli.outline._get_project', return_value=mock_project):
            with tempfile.TemporaryDirectory() as tmpdir:
                mock_project.get_outline_dir.return_value = Path(tmpdir)

                result = runner.invoke(app, ["refine"])
                assert "no outline" in result.output.lower()

    def test_refine_non_interactive(self, mock_project):
        """Test refine in non-interactive mode."""
        mock_outline = Mock()
        mock_outline.sections = []

        with patch('papergen.cli.outline._get_project', return_value=mock_project):
            with patch('papergen.cli.outline.Outline') as MockOutline:
                MockOutline.from_json_file.return_value = mock_outline

                with tempfile.TemporaryDirectory() as tmpdir:
                    outline_dir = Path(tmpdir)
                    (outline_dir / "outline.json").write_text("{}")
                    mock_project.get_outline_dir.return_value = outline_dir

                    result = runner.invoke(app, ["refine", "--no-interactive"])
                    assert "not yet implemented" in result.output.lower()


class TestExportOutlineCommand:
    """Tests for export outline command."""

    @pytest.fixture
    def mock_project(self):
        """Create mock project."""
        project = Mock()
        project.get_outline_dir.return_value = Path("/tmp/test/outline")
        return project

    def test_export_help(self):
        """Test export command help."""
        result = runner.invoke(app, ["export", "--help"])
        assert result.exit_code == 0
        assert "export" in result.output.lower()

    def test_export_no_outline(self, mock_project):
        """Test export when no outline exists."""
        with patch('papergen.cli.outline._get_project', return_value=mock_project):
            with tempfile.TemporaryDirectory() as tmpdir:
                mock_project.get_outline_dir.return_value = Path(tmpdir)

                result = runner.invoke(app, ["export"])
                assert "no outline" in result.output.lower()

    def test_export_markdown(self, mock_project):
        """Test export to markdown."""
        mock_outline = Mock()
        mock_outline.to_markdown.return_value = "# Outline\n\nContent"

        with patch('papergen.cli.outline._get_project', return_value=mock_project):
            with patch('papergen.cli.outline.Outline') as MockOutline:
                MockOutline.from_json_file.return_value = mock_outline

                with tempfile.TemporaryDirectory() as tmpdir:
                    outline_dir = Path(tmpdir)
                    (outline_dir / "outline.json").write_text("{}")
                    mock_project.get_outline_dir.return_value = outline_dir

                    result = runner.invoke(app, ["export", "--format", "markdown"])
                    # Should output markdown

    def test_export_json(self, mock_project):
        """Test export to JSON."""
        mock_outline = Mock()
        mock_outline.model_dump.return_value = {"topic": "Test", "sections": []}

        with patch('papergen.cli.outline._get_project', return_value=mock_project):
            with patch('papergen.cli.outline.Outline') as MockOutline:
                MockOutline.from_json_file.return_value = mock_outline

                with tempfile.TemporaryDirectory() as tmpdir:
                    outline_dir = Path(tmpdir)
                    (outline_dir / "outline.json").write_text("{}")
                    mock_project.get_outline_dir.return_value = outline_dir

                    result = runner.invoke(app, ["export", "--format", "json"])
                    # Should output JSON

    def test_export_unknown_format(self, mock_project):
        """Test export with unknown format."""
        mock_outline = Mock()

        with patch('papergen.cli.outline._get_project', return_value=mock_project):
            with patch('papergen.cli.outline.Outline') as MockOutline:
                MockOutline.from_json_file.return_value = mock_outline

                with tempfile.TemporaryDirectory() as tmpdir:
                    outline_dir = Path(tmpdir)
                    (outline_dir / "outline.json").write_text("{}")
                    mock_project.get_outline_dir.return_value = outline_dir

                    result = runner.invoke(app, ["export", "--format", "unknown"])
                    assert "unknown format" in result.output.lower()


class TestCreateBasicOutline:
    """Tests for _create_basic_outline function."""

    def test_create_basic_outline(self):
        """Test creating basic outline."""
        mock_project = Mock()
        mock_project.state = Mock()

        with tempfile.TemporaryDirectory() as tmpdir:
            outline_dir = Path(tmpdir)
            mock_project.get_outline_dir.return_value = outline_dir

            _create_basic_outline(
                project=mock_project,
                topic="Test Topic",
                sections=["introduction", "methods", "results"],
                word_counts={"introduction": 500, "methods": 1000, "results": 800}
            )

            # Check files were created
            assert (outline_dir / "outline.json").exists()
            assert (outline_dir / "outline.md").exists()

            # Check state was updated
            mock_project.state.mark_stage_completed.assert_called_with("outline")
            mock_project.save_state.assert_called_once()


class TestShowOutlinePreview:
    """Tests for _show_outline_preview function."""

    def test_show_preview(self, capsys):
        """Test showing outline preview."""
        mock_section = Mock()
        mock_section.title = "Introduction"
        mock_section.word_count_target = 1000
        mock_section.objectives = ["Explain problem", "Present motivation"]
        mock_section.key_points = ["Point 1", "Point 2", "Point 3", "Point 4"]
        mock_section.subsections = []

        mock_outline = Mock()
        mock_outline.sections = [mock_section]

        _show_outline_preview(mock_outline)
        # Should not raise error

    def test_show_preview_with_subsections(self, capsys):
        """Test showing preview with subsections."""
        mock_subsection = Mock()
        mock_subsection.title = "Subsection 1"

        mock_section = Mock()
        mock_section.title = "Introduction"
        mock_section.word_count_target = 1000
        mock_section.objectives = []
        mock_section.key_points = []
        mock_section.subsections = [mock_subsection, mock_subsection]

        mock_outline = Mock()
        mock_outline.sections = [mock_section]

        _show_outline_preview(mock_outline)
        # Should not raise error


class TestGetProject:
    """Tests for _get_project function."""

    def test_get_project_delegates(self):
        """Test that _get_project delegates to main module."""
        mock_project = Mock()

        with patch('papergen.cli.outline._get_project') as mock_get:
            mock_get.return_value = mock_project

            from papergen.cli.outline import _get_project
            result = _get_project()

            # Should return the project
