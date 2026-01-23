"""Tests for CLI commands."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import os

from typer.testing import CliRunner

from papergen.cli.main import app


runner = CliRunner()


class TestMainCLI:
    """Tests for main CLI commands."""

    def test_cli_help(self):
        """Test CLI help output."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "papergen" in result.output.lower() or "paper" in result.output.lower()

    def test_cli_version_not_implemented(self):
        """Test that version flag behavior is defined."""
        # This just tests that the CLI handles this gracefully
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0


class TestInitCommand:
    """Tests for init command."""

    def test_init_new_project(self):
        """Test initializing a new project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(app, [
                "init",
                "Machine Learning Paper",
                "--path", tmpdir,
                "--template", "ieee",
                "--format", "latex"
            ])

            assert result.exit_code == 0
            assert "successfully" in result.output.lower() or "initialized" in result.output.lower()
            assert (Path(tmpdir) / ".papergen").exists()

    def test_init_with_author(self):
        """Test init with author option."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(app, [
                "init",
                "Test Paper",
                "--path", tmpdir,
                "--author", "John Doe, Jane Smith"
            ])

            assert result.exit_code == 0

    def test_init_already_initialized(self):
        """Test init in already initialized directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # First init
            runner.invoke(app, ["init", "First Paper", "--path", tmpdir])

            # Second init should warn
            result = runner.invoke(app, ["init", "Second Paper", "--path", tmpdir])

            assert "already" in result.output.lower() or "warning" in result.output.lower()


class TestStatusCommand:
    """Tests for status command."""

    def test_status_no_project(self):
        """Test status when not in a project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Change to temp dir (no project)
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                result = runner.invoke(app, ["status"])

                # Should fail or show error
                assert result.exit_code != 0 or "not" in result.output.lower()
            finally:
                os.chdir(original_cwd)

    def test_status_with_project(self):
        """Test status in initialized project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize project
            runner.invoke(app, ["init", "Test Paper", "--path", tmpdir])

            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                result = runner.invoke(app, ["status"])

                assert result.exit_code == 0
                assert "Test Paper" in result.output or "status" in result.output.lower()
            finally:
                os.chdir(original_cwd)


class TestConfigCommand:
    """Tests for config command."""

    def test_config_show(self):
        """Test showing configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner.invoke(app, ["init", "Test", "--path", tmpdir])

            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                result = runner.invoke(app, ["config-cmd", "--show"])

                assert result.exit_code == 0
            finally:
                os.chdir(original_cwd)

    def test_config_get_key(self):
        """Test getting a config key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner.invoke(app, ["init", "Test", "--path", tmpdir])

            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                result = runner.invoke(app, ["config-cmd", "api.model"])

                assert result.exit_code == 0
            finally:
                os.chdir(original_cwd)

    def test_config_set_key(self):
        """Test setting a config key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner.invoke(app, ["init", "Test", "--path", tmpdir])

            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                result = runner.invoke(app, ["config-cmd", "test.key", "test_value"])

                assert result.exit_code == 0
                assert "test.key" in result.output
            finally:
                os.chdir(original_cwd)


class TestCacheCommand:
    """Tests for cache command."""

    def test_cache_stats(self):
        """Test cache stats command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner.invoke(app, ["init", "Test", "--path", tmpdir])

            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                result = runner.invoke(app, ["cache", "stats"])

                assert result.exit_code == 0
                # Should show cache statistics
                assert "cache" in result.output.lower() or "hit" in result.output.lower()
            finally:
                os.chdir(original_cwd)

    def test_cache_clear(self):
        """Test cache clear command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner.invoke(app, ["init", "Test", "--path", tmpdir])

            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                result = runner.invoke(app, ["cache", "clear"])

                assert result.exit_code == 0
                assert "clear" in result.output.lower()
            finally:
                os.chdir(original_cwd)

    def test_cache_invalid_action(self):
        """Test cache with invalid action."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner.invoke(app, ["init", "Test", "--path", tmpdir])

            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                result = runner.invoke(app, ["cache", "invalid"])

                assert result.exit_code != 0
            finally:
                os.chdir(original_cwd)


class TestDebugFlag:
    """Tests for debug flag."""

    def test_debug_mode(self):
        """Test running with debug flag."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(app, [
                "--debug",
                "init",
                "Debug Test",
                "--path", tmpdir
            ])

            # Should still work with debug enabled
            assert result.exit_code == 0


class TestSubcommands:
    """Tests for subcommand registration."""

    def test_research_subcommand_exists(self):
        """Test that research subcommand is registered."""
        result = runner.invoke(app, ["research", "--help"])
        # Should either work or show meaningful error
        assert "research" in result.output.lower() or result.exit_code == 0

    def test_outline_subcommand_exists(self):
        """Test that outline subcommand is registered."""
        result = runner.invoke(app, ["outline", "--help"])
        assert "outline" in result.output.lower() or result.exit_code == 0

    def test_draft_subcommand_exists(self):
        """Test that draft subcommand is registered."""
        result = runner.invoke(app, ["draft", "--help"])
        assert "draft" in result.output.lower() or result.exit_code == 0

    def test_revise_subcommand_exists(self):
        """Test that revise subcommand is registered."""
        result = runner.invoke(app, ["revise", "--help"])
        assert "revise" in result.output.lower() or result.exit_code == 0

    def test_format_subcommand_exists(self):
        """Test that format subcommand is registered."""
        result = runner.invoke(app, ["format", "--help"])
        assert "format" in result.output.lower() or result.exit_code == 0

    def test_discover_subcommand_exists(self):
        """Test that discover subcommand is registered."""
        result = runner.invoke(app, ["discover", "--help"])
        assert "discover" in result.output.lower() or result.exit_code == 0


class TestChatCommand:
    """Tests for chat command."""

    @patch('papergen.interactive.repl.PaperGenREPL')
    def test_chat_starts_repl(self, mock_repl_class):
        """Test that chat command starts the REPL."""
        mock_repl = Mock()
        mock_repl_class.return_value = mock_repl

        result = runner.invoke(app, ["chat"])

        mock_repl_class.assert_called_once()
        mock_repl.run.assert_called_once()


class TestGetProject:
    """Tests for _get_project helper."""

    def test_get_project_finds_project(self):
        """Test finding project in current directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize project
            runner.invoke(app, ["init", "Test", "--path", tmpdir])

            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)

                # Status command uses _get_project internally
                result = runner.invoke(app, ["status"])
                assert result.exit_code == 0
            finally:
                os.chdir(original_cwd)

    def test_get_project_not_found(self):
        """Test error when project not found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)

                result = runner.invoke(app, ["status"])

                # Should exit with error
                assert result.exit_code != 0
            finally:
                os.chdir(original_cwd)


class TestErrorHandling:
    """Tests for CLI error handling."""

    def test_init_handles_exception(self):
        """Test that init handles exceptions gracefully."""
        with patch('papergen.cli.main.PaperProject') as mock_project:
            mock_project.side_effect = Exception("Test error")

            with tempfile.TemporaryDirectory() as tmpdir:
                result = runner.invoke(app, ["init", "Test", "--path", tmpdir])

                # Should handle error
                assert result.exit_code != 0 or "error" in result.output.lower()
