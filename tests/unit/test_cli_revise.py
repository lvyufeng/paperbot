"""Tests for revise CLI commands."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
from datetime import datetime

from typer.testing import CliRunner

from papergen.cli.revise import app


runner = CliRunner()


class TestReviseSectionCommand:
    """Tests for revise section command."""

    @pytest.fixture
    def mock_project(self):
        """Create mock project."""
        project = Mock()
        project.root_path = Path("/tmp/test")
        project.get_research_dir.return_value = Path("/tmp/test/research")
        return project

    @pytest.fixture
    def mock_draft(self):
        """Create mock draft."""
        draft = Mock()
        draft.metadata = {'section_title': 'Introduction'}
        draft.version = 1
        draft.word_count = 500
        draft.content = "Original content"
        draft.citation_keys = []
        return draft

    def test_revise_section_help(self):
        """Test revise section help."""
        result = runner.invoke(app, ["revise-section", "--help"])
        assert result.exit_code == 0
        assert "section" in result.output.lower()


class TestReviseAllCommand:
    """Tests for revise all command."""

    @pytest.fixture
    def mock_project(self):
        """Create mock project."""
        project = Mock()
        project.root_path = Path("/tmp/test")
        project.state = Mock()
        project.get_research_dir.return_value = Path("/tmp/test/research")
        project.save_state = Mock()
        return project

    def test_revise_all_ai_disabled(self, mock_project):
        """Test revise all with AI disabled."""
        with patch('papergen.cli.revise._get_project', return_value=mock_project):
            result = runner.invoke(app, ["all", "--feedback", "Improve", "--no-use-ai"])
            assert "ai disabled" in result.output.lower()

    def test_revise_all_no_drafts(self, mock_project):
        """Test revise all when no drafts exist."""
        mock_manager = Mock()
        mock_manager.list_drafts.return_value = []

        with patch('papergen.cli.revise._get_project', return_value=mock_project):
            with patch('papergen.cli.revise.SectionManager', return_value=mock_manager):
                result = runner.invoke(app, ["all", "--feedback", "Improve"])
                assert "no drafts" in result.output.lower()

    def test_revise_all_skip_sections(self, mock_project):
        """Test revise all with skipped sections."""
        mock_manager = Mock()
        mock_manager.list_drafts.return_value = ['intro', 'methods', 'results']

        with patch('papergen.cli.revise._get_project', return_value=mock_project):
            with patch('papergen.cli.revise.SectionManager', return_value=mock_manager):
                result = runner.invoke(app, [
                    "all",
                    "--feedback", "Test",
                    "--skip-sections", "intro,methods,results"
                ])
                assert "all sections skipped" in result.output.lower()


class TestCompareVersionsCommand:
    """Tests for compare versions command."""

    @pytest.fixture
    def mock_project(self):
        """Create mock project."""
        project = Mock()
        project.root_path = Path("/tmp/test")
        return project

    def test_compare_no_draft(self, mock_project):
        """Test compare when no draft exists."""
        mock_manager = Mock()
        mock_manager.load_draft.return_value = None

        with patch('papergen.cli.revise._get_project', return_value=mock_project):
            with patch('papergen.cli.revise.SectionManager', return_value=mock_manager):
                result = runner.invoke(app, ["compare", "intro"])
                assert result.exit_code != 0

    def test_compare_no_history(self, mock_project):
        """Test compare when no version history."""
        mock_draft = Mock()
        mock_draft.version = 1

        mock_manager = Mock()
        mock_manager.load_draft.return_value = mock_draft
        mock_manager.get_version_history.return_value = []

        with patch('papergen.cli.revise._get_project', return_value=mock_project):
            with patch('papergen.cli.revise.SectionManager', return_value=mock_manager):
                result = runner.invoke(app, ["compare", "intro"])
                assert "no version history" in result.output.lower()

    def test_compare_single_version(self, mock_project):
        """Test compare when only one version exists."""
        mock_draft = Mock()
        mock_draft.version = 1

        mock_manager = Mock()
        mock_manager.load_draft.return_value = mock_draft
        mock_manager.get_version_history.return_value = [1]

        with patch('papergen.cli.revise._get_project', return_value=mock_project):
            with patch('papergen.cli.revise.SectionManager', return_value=mock_manager):
                result = runner.invoke(app, ["compare", "intro"])
                assert "only one version" in result.output.lower()


class TestRevertCommand:
    """Tests for revert command."""

    @pytest.fixture
    def mock_project(self):
        """Create mock project."""
        project = Mock()
        project.root_path = Path("/tmp/test")
        return project

    def test_revert_no_draft(self, mock_project):
        """Test revert when no draft exists."""
        mock_manager = Mock()
        mock_manager.load_draft.return_value = None

        with patch('papergen.cli.revise._get_project', return_value=mock_project):
            with patch('papergen.cli.revise.SectionManager', return_value=mock_manager):
                result = runner.invoke(app, ["revert", "intro", "1"])
                assert result.exit_code != 0

    def test_revert_version_not_found(self, mock_project):
        """Test revert to nonexistent version."""
        mock_draft = Mock()
        mock_draft.version = 3

        mock_manager = Mock()
        mock_manager.load_draft.return_value = mock_draft
        mock_manager.versions_dir = Path("/tmp/test/versions")
        mock_manager.get_version_history.return_value = [1, 2, 3]

        with patch('papergen.cli.revise._get_project', return_value=mock_project):
            with patch('papergen.cli.revise.SectionManager', return_value=mock_manager):
                result = runner.invoke(app, ["revert", "intro", "99"])
                assert "not found" in result.output.lower()


class TestHistoryCommand:
    """Tests for history command."""

    @pytest.fixture
    def mock_project(self):
        """Create mock project."""
        project = Mock()
        project.root_path = Path("/tmp/test")
        return project

    def test_history_no_draft(self, mock_project):
        """Test history when no draft exists."""
        mock_manager = Mock()
        mock_manager.load_draft.return_value = None

        with patch('papergen.cli.revise._get_project', return_value=mock_project):
            with patch('papergen.cli.revise.SectionManager', return_value=mock_manager):
                result = runner.invoke(app, ["history", "intro"])
                assert result.exit_code != 0

    def test_history_no_versions(self, mock_project):
        """Test history when no version history."""
        mock_draft = Mock()
        mock_draft.version = 1
        mock_draft.citation_keys = []
        mock_draft.updated_at = datetime.now()

        mock_manager = Mock()
        mock_manager.load_draft.return_value = mock_draft
        mock_manager.get_version_history.return_value = []

        with patch('papergen.cli.revise._get_project', return_value=mock_project):
            with patch('papergen.cli.revise.SectionManager', return_value=mock_manager):
                result = runner.invoke(app, ["history", "intro"])
                assert "no version history" in result.output.lower()

    def test_history_with_versions(self, mock_project):
        """Test history with multiple versions."""
        mock_draft = Mock()
        mock_draft.version = 2
        mock_draft.citation_keys = ['cite1']
        mock_draft.updated_at = datetime.now()

        mock_manager = Mock()
        mock_manager.load_draft.return_value = mock_draft
        mock_manager.get_version_history.return_value = [1, 2]

        with patch('papergen.cli.revise._get_project', return_value=mock_project):
            with patch('papergen.cli.revise.SectionManager', return_value=mock_manager):
                with tempfile.TemporaryDirectory() as tmpdir:
                    versions_dir = Path(tmpdir)
                    mock_manager.versions_dir = versions_dir

                    # Create version files
                    v1_file = versions_dir / "intro_v1.md"
                    v2_file = versions_dir / "intro_v2.md"
                    v1_file.write_text("Version 1 content")
                    v2_file.write_text("Version 2 content with more words")

                    result = runner.invoke(app, ["history", "intro"])
                    assert result.exit_code == 0
                    assert "version" in result.output.lower()


class TestPolishCommand:
    """Tests for polish command."""

    @pytest.fixture
    def mock_project(self):
        """Create mock project."""
        project = Mock()
        project.root_path = Path("/tmp/test")
        project.get_research_dir.return_value = Path("/tmp/test/research")
        return project

    def test_polish_no_draft(self, mock_project):
        """Test polish when no draft exists."""
        mock_manager = Mock()
        mock_manager.load_draft.return_value = None

        with patch('papergen.cli.revise._get_project', return_value=mock_project):
            with patch('papergen.cli.revise.SectionManager', return_value=mock_manager):
                result = runner.invoke(app, ["polish", "intro"])
                assert result.exit_code != 0

    def test_polish_ai_disabled(self, mock_project):
        """Test polish with AI disabled."""
        mock_draft = Mock()
        mock_draft.metadata = {'section_title': 'Intro'}
        mock_draft.version = 1

        mock_manager = Mock()
        mock_manager.load_draft.return_value = mock_draft

        with patch('papergen.cli.revise._get_project', return_value=mock_project):
            with patch('papergen.cli.revise.SectionManager', return_value=mock_manager):
                result = runner.invoke(app, ["polish", "intro", "--no-use-ai"])
                assert "ai disabled" in result.output.lower()
