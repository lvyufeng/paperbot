"""Tests for InputHandler and CommandCompleter."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile


class TestCommandCompleter:
    """Tests for CommandCompleter."""

    def test_completer_has_commands(self):
        """Test completer has commands."""
        from papergen.interactive.input_handler import CommandCompleter
        completer = CommandCompleter()

        assert '/help' in completer.COMMANDS
        assert '/exit' in completer.COMMANDS
        assert '/quit' in completer.COMMANDS

    def test_get_completions_with_slash(self):
        """Test completions when text starts with slash."""
        from papergen.interactive.input_handler import CommandCompleter
        completer = CommandCompleter()

        mock_document = Mock()
        mock_document.text_before_cursor = "/he"

        completions = list(completer.get_completions(mock_document, None))

        # Should match /help and /history
        completion_texts = [c.text for c in completions]
        assert '/help' in completion_texts

    def test_get_completions_without_slash(self):
        """Test no completions without slash."""
        from papergen.interactive.input_handler import CommandCompleter
        completer = CommandCompleter()

        mock_document = Mock()
        mock_document.text_before_cursor = "help"

        completions = list(completer.get_completions(mock_document, None))

        assert len(completions) == 0

    def test_get_completions_full_command(self):
        """Test completions with full command."""
        from papergen.interactive.input_handler import CommandCompleter
        completer = CommandCompleter()

        mock_document = Mock()
        mock_document.text_before_cursor = "/help"

        completions = list(completer.get_completions(mock_document, None))

        # Should still match /help
        assert len(completions) >= 1


class TestInputHandlerInit:
    """Tests for InputHandler initialization."""

    def test_init_default_history(self):
        """Test init with default history file."""
        from papergen.interactive.input_handler import InputHandler
        handler = InputHandler()

        assert handler.history_file is not None
        assert ".papergen" in str(handler.history_file)
        assert handler.session is None

    def test_init_custom_history(self):
        """Test init with custom history file."""
        from papergen.interactive.input_handler import InputHandler

        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / "custom_history"
            handler = InputHandler(history_file=history_file)

            assert handler.history_file == history_file


class TestInputHandlerDefaultHistory:
    """Tests for _get_default_history method."""

    def test_get_default_history(self):
        """Test getting default history path."""
        from papergen.interactive.input_handler import InputHandler
        handler = InputHandler()

        result = handler._get_default_history()

        assert isinstance(result, Path)
        assert "papergen" in str(result)
        assert "chat_history" in str(result)


class TestInputHandlerInitialize:
    """Tests for initialize method."""

    def test_initialize_creates_session(self):
        """Test initialize creates prompt session."""
        from papergen.interactive.input_handler import InputHandler

        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / "history"
            handler = InputHandler(history_file=history_file)

            handler.initialize()

            assert handler.session is not None


class TestInputHandlerPrompt:
    """Tests for prompt method."""

    def test_prompt_initializes_if_needed(self):
        """Test prompt initializes session if needed."""
        from papergen.interactive.input_handler import InputHandler

        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / "history"
            handler = InputHandler(history_file=history_file)

            assert handler.session is None

            # Mock the session to avoid actual prompt
            mock_session = Mock()
            mock_session.prompt.return_value = "test input"

            with patch.object(handler, 'initialize'):
                handler.session = mock_session
                result = handler.prompt("Test > ")

            assert result == "test input"

    def test_prompt_multiline(self):
        """Test multiline prompt."""
        from papergen.interactive.input_handler import InputHandler

        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / "history"
            handler = InputHandler(history_file=history_file)

            mock_session = Mock()
            mock_session.prompt.return_value = "line 1\nline 2"

            with patch.object(handler, 'initialize'):
                handler.session = mock_session
                result = handler.prompt_multiline("Test > ")

            assert result == "line 1\nline 2"
            mock_session.prompt.assert_called_with("Test > ", multiline=True)
