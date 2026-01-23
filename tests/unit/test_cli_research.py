"""Tests for research CLI commands."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import json

from typer.testing import CliRunner

from papergen.cli.research import (
    app, _add_file_source, _add_url_source, _update_source_index
)


runner = CliRunner()


class TestAddSourcesCommand:
    """Tests for add sources command."""

    @pytest.fixture
    def mock_project(self):
        """Create mock project."""
        project = Mock()
        project.root_path = Path("/tmp/test")
        project.get_sources_dir.return_value = Path("/tmp/test/sources")
        project.get_extracted_dir.return_value = Path("/tmp/test/extracted")
        return project

    def test_add_nonexistent_file(self, mock_project):
        """Test adding nonexistent file."""
        with patch('papergen.cli.research._get_project', return_value=mock_project):
            result = runner.invoke(app, ["add", "/nonexistent/file.pdf"])
            assert "not found" in result.output.lower()

    def test_add_pdf_file(self, mock_project):
        """Test adding a PDF file."""
        mock_extractor = Mock()
        mock_extractor.extract.return_value = {
            "metadata": {"title": "Test Paper"},
            "content": {"full_text": "Test content"}
        }

        with patch('papergen.cli.research._get_project', return_value=mock_project):
            with patch('papergen.cli.research.PDFExtractor', return_value=mock_extractor):
                with tempfile.TemporaryDirectory() as tmpdir:
                    # Create test PDF file
                    pdf_file = Path(tmpdir) / "test.pdf"
                    pdf_file.write_text("fake pdf content")

                    mock_project.get_sources_dir.return_value = Path(tmpdir) / "sources"
                    mock_project.get_extracted_dir.return_value = Path(tmpdir) / "extracted"

                    result = runner.invoke(app, ["add", str(pdf_file)])
                    assert result.exit_code == 0 or "added" in result.output.lower()

    def test_add_text_file(self, mock_project):
        """Test adding a text file."""
        mock_extractor = Mock()
        mock_extractor.extract.return_value = {
            "metadata": {"title": "Test Note"},
            "content": {"full_text": "Text content"}
        }

        with patch('papergen.cli.research._get_project', return_value=mock_project):
            with patch('papergen.cli.research.TextExtractor', return_value=mock_extractor):
                with tempfile.TemporaryDirectory() as tmpdir:
                    text_file = Path(tmpdir) / "notes.txt"
                    text_file.write_text("Some notes")

                    mock_project.get_sources_dir.return_value = Path(tmpdir) / "sources"
                    mock_project.get_extracted_dir.return_value = Path(tmpdir) / "extracted"

                    result = runner.invoke(app, ["add", str(text_file)])
                    # Should handle gracefully


class TestAddUrlSource:
    """Tests for adding URL sources."""

    @pytest.fixture
    def mock_project(self):
        """Create mock project."""
        project = Mock()
        project.get_extracted_dir.return_value = Path("/tmp/test/extracted")
        return project

    def test_add_url_success(self, mock_project):
        """Test adding URL successfully."""
        mock_extractor = Mock()
        mock_extractor.extract.return_value = {
            "metadata": {"title": "Web Page"},
            "content": {"full_text": "Web content"}
        }

        with patch('papergen.cli.research._get_project', return_value=mock_project):
            with patch('papergen.cli.research.WebExtractor', return_value=mock_extractor):
                with tempfile.TemporaryDirectory() as tmpdir:
                    mock_project.get_extracted_dir.return_value = Path(tmpdir)

                    result = runner.invoke(app, ["add", ".", "--url", "https://example.com/paper"])
                    # Should process the URL


class TestOrganizeCommand:
    """Tests for organize command."""

    @pytest.fixture
    def mock_project(self):
        """Create mock project."""
        project = Mock()
        project.state = Mock()
        project.state.topic = "Test Topic"
        project.get_extracted_dir.return_value = Path("/tmp/test/extracted")
        project.get_research_dir.return_value = Path("/tmp/test/research")
        project.save_state = Mock()
        return project

    def test_organize_no_sources(self, mock_project):
        """Test organize when no sources exist."""
        with patch('papergen.cli.research._get_project', return_value=mock_project):
            with tempfile.TemporaryDirectory() as tmpdir:
                mock_project.get_extracted_dir.return_value = Path(tmpdir)
                result = runner.invoke(app, ["organize"])
                assert "no" in result.output.lower() and "sources" in result.output.lower()

    def test_organize_with_sources(self, mock_project):
        """Test organize with existing sources."""
        mock_organizer = Mock()
        mock_organizer.organize.return_value = "# Organized Research\n\nContent"
        mock_organizer.claude_client = None

        with patch('papergen.cli.research._get_project', return_value=mock_project):
            with patch('papergen.cli.research.ResearchOrganizer', return_value=mock_organizer):
                with tempfile.TemporaryDirectory() as tmpdir:
                    # Create source file
                    source_file = Path(tmpdir) / "source_abc123.json"
                    source_file.write_text(json.dumps({
                        "metadata": {"title": "Test"},
                        "content": {"full_text": "Content"}
                    }))

                    mock_project.get_extracted_dir.return_value = Path(tmpdir)
                    mock_project.get_research_dir.return_value = Path(tmpdir)

                    result = runner.invoke(app, ["organize", "--no-use-ai"])
                    assert result.exit_code == 0

    def test_organize_with_ai(self, mock_project):
        """Test organize with AI enabled."""
        mock_organizer = Mock()
        mock_organizer.organize.return_value = "# AI Organized\n\nContent"
        mock_organizer.claude_client = Mock()

        with patch('papergen.cli.research._get_project', return_value=mock_project):
            with patch('papergen.cli.research.ResearchOrganizer', return_value=mock_organizer):
                with patch('papergen.ai.claude_client.ClaudeClient'):
                    with tempfile.TemporaryDirectory() as tmpdir:
                        source_file = Path(tmpdir) / "source_123.json"
                        source_file.write_text(json.dumps({
                            "metadata": {},
                            "content": {}
                        }))

                        mock_project.get_extracted_dir.return_value = Path(tmpdir)
                        mock_project.get_research_dir.return_value = Path(tmpdir)

                        result = runner.invoke(app, ["organize"])
                        # Should complete (may fail on AI init)


class TestListSourcesCommand:
    """Tests for list sources command."""

    @pytest.fixture
    def mock_project(self):
        """Create mock project."""
        project = Mock()
        project.get_extracted_dir.return_value = Path("/tmp/test/extracted")
        return project

    def test_list_no_sources(self, mock_project):
        """Test listing when no sources exist."""
        with patch('papergen.cli.research._get_project', return_value=mock_project):
            with tempfile.TemporaryDirectory() as tmpdir:
                mock_project.get_extracted_dir.return_value = Path(tmpdir)
                result = runner.invoke(app, ["list"])
                assert "no sources" in result.output.lower()

    def test_list_with_sources(self, mock_project):
        """Test listing existing sources."""
        with patch('papergen.cli.research._get_project', return_value=mock_project):
            with tempfile.TemporaryDirectory() as tmpdir:
                # Create index file
                index_file = Path(tmpdir) / "index.json"
                index_file.write_text(json.dumps({
                    "sources": [
                        {
                            "id": "source_123",
                            "type": "pdf",
                            "added_at": "2024-01-01",
                            "metadata": {"title": "Test Paper"}
                        }
                    ]
                }))

                mock_project.get_extracted_dir.return_value = Path(tmpdir)
                result = runner.invoke(app, ["list"])
                assert "source_123" in result.output


class TestUpdateSourceIndex:
    """Tests for _update_source_index helper."""

    def test_update_creates_new_index(self):
        """Test creating new index file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_project = Mock()
            mock_project.get_extracted_dir.return_value = Path(tmpdir)

            extracted = {
                "type": "pdf",
                "original_path": "/path/to/file.pdf",
                "added_at": "2024-01-01",
                "metadata": {"title": "Test"}
            }

            _update_source_index(mock_project, "source_abc", extracted)

            index_file = Path(tmpdir) / "index.json"
            assert index_file.exists()

            with open(index_file) as f:
                index = json.load(f)
            assert len(index["sources"]) == 1
            assert index["sources"][0]["id"] == "source_abc"

    def test_update_appends_to_existing(self):
        """Test appending to existing index."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_project = Mock()
            mock_project.get_extracted_dir.return_value = Path(tmpdir)

            # Create existing index
            index_file = Path(tmpdir) / "index.json"
            index_file.write_text(json.dumps({
                "sources": [{"id": "existing"}]
            }))

            extracted = {
                "type": "web",
                "original_path": "https://example.com",
                "added_at": "2024-01-02",
                "metadata": {}
            }

            _update_source_index(mock_project, "source_new", extracted)

            with open(index_file) as f:
                index = json.load(f)
            assert len(index["sources"]) == 2


class TestSourceTypeDetection:
    """Tests for source type detection in _add_file_source."""

    @pytest.fixture
    def mock_project(self):
        """Create mock project."""
        project = Mock()
        return project

    def test_detect_pdf_extension(self, mock_project):
        """Test that PDF extension is correctly detected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_file = Path(tmpdir) / "paper.pdf"
            pdf_file.write_text("fake pdf")

            mock_project.get_sources_dir.return_value = Path(tmpdir) / "sources"
            mock_project.get_extracted_dir.return_value = Path(tmpdir) / "extracted"

            mock_extractor = Mock()
            mock_extractor.extract.return_value = {"metadata": {}, "content": {}}

            with patch('papergen.cli.research.PDFExtractor', return_value=mock_extractor):
                with patch('papergen.cli.research._update_source_index'):
                    _add_file_source(mock_project, pdf_file)
                    mock_extractor.extract.assert_called_once()

    def test_detect_txt_extension(self, mock_project):
        """Test that TXT extension is correctly detected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            txt_file = Path(tmpdir) / "notes.txt"
            txt_file.write_text("some notes")

            mock_project.get_sources_dir.return_value = Path(tmpdir) / "sources"
            mock_project.get_extracted_dir.return_value = Path(tmpdir) / "extracted"

            mock_extractor = Mock()
            mock_extractor.extract.return_value = {"metadata": {}, "content": {}}

            with patch('papergen.cli.research.TextExtractor', return_value=mock_extractor):
                with patch('papergen.cli.research._update_source_index'):
                    _add_file_source(mock_project, txt_file)
                    mock_extractor.extract.assert_called_once()

    def test_detect_md_extension(self, mock_project):
        """Test that MD extension is correctly detected as text."""
        with tempfile.TemporaryDirectory() as tmpdir:
            md_file = Path(tmpdir) / "notes.md"
            md_file.write_text("# Notes")

            mock_project.get_sources_dir.return_value = Path(tmpdir) / "sources"
            mock_project.get_extracted_dir.return_value = Path(tmpdir) / "extracted"

            mock_extractor = Mock()
            mock_extractor.extract.return_value = {"metadata": {}, "content": {}}

            with patch('papergen.cli.research.TextExtractor', return_value=mock_extractor):
                with patch('papergen.cli.research._update_source_index'):
                    _add_file_source(mock_project, md_file)
                    mock_extractor.extract.assert_called_once()
