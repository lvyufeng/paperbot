"""Tests for REPL module."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from papergen.interactive.repl import PaperGenREPL
from papergen.interactive.tools.base import ToolResult, ToolSafety


class TestPaperGenREPLInit:
    """Tests for REPL initialization."""

    def test_init(self):
        """Test REPL initialization."""
        repl = PaperGenREPL()

        assert repl.tools == {}
        assert repl.running is False
        assert repl.provider == "anthropic"


class TestPaperGenREPLTools:
    """Tests for tool management."""

    @pytest.fixture
    def repl(self):
        """Create REPL instance."""
        return PaperGenREPL()

    def test_register_tool(self, repl):
        """Test registering a tool."""
        mock_tool = Mock()
        mock_tool.name = "test_tool"

        repl.register_tool(mock_tool)

        assert "test_tool" in repl.tools
        assert repl.tools["test_tool"] == mock_tool

    def test_load_default_tools(self, repl):
        """Test loading default tools."""
        with patch('papergen.interactive.tools.file_tools.ReadFileTool') as mock_read:
            with patch('papergen.interactive.tools.file_tools.WriteFileTool') as mock_write:
                with patch('papergen.interactive.tools.file_tools.SearchFilesTool') as mock_search:
                    with patch('papergen.interactive.tools.paper_tools.AnalyzePDFTool') as mock_pdf:
                        with patch('papergen.interactive.tools.paper_tools.SearchPapersTool') as mock_papers:
                            # Set up mock tool names
                            mock_read.return_value.name = "read_file"
                            mock_write.return_value.name = "write_file"
                            mock_search.return_value.name = "search_files"
                            mock_pdf.return_value.name = "analyze_pdf"
                            mock_papers.return_value.name = "search_papers"

                            repl._load_default_tools()

                            assert len(repl.tools) == 5

    def test_get_tool_schemas(self, repl):
        """Test getting tool schemas."""
        mock_tool = Mock()
        mock_tool.name = "test"
        mock_tool.get_schema.return_value = {"name": "test", "type": "function"}

        repl.register_tool(mock_tool)
        schemas = repl._get_tool_schemas()

        assert len(schemas) == 1
        assert schemas[0]["name"] == "test"


class TestPaperGenREPLToolExecution:
    """Tests for tool execution."""

    @pytest.fixture
    def repl(self):
        """Create REPL with mock tool."""
        r = PaperGenREPL()
        mock_tool = Mock()
        mock_tool.name = "test_tool"
        mock_tool.safety = ToolSafety.SAFE
        mock_tool.execute.return_value = ToolResult(True, "Success")
        r.tools["test_tool"] = mock_tool
        return r

    def test_execute_known_tool(self, repl):
        """Test executing a known tool."""
        result = repl._execute_tool("test_tool", {"arg": "value"})

        assert result.success is True
        assert result.output == "Success"

    def test_execute_unknown_tool(self, repl):
        """Test executing unknown tool."""
        result = repl._execute_tool("unknown_tool", {})

        assert result.success is False
        assert "Unknown tool" in result.error

    def test_execute_moderate_safety_tool_confirmed(self, repl):
        """Test executing moderate safety tool with confirmation."""
        moderate_tool = Mock()
        moderate_tool.name = "moderate_tool"
        moderate_tool.safety = ToolSafety.MODERATE
        moderate_tool.execute.return_value = ToolResult(True, "Done")
        repl.tools["moderate_tool"] = moderate_tool

        with patch.object(repl, '_confirm_tool', return_value=True):
            result = repl._execute_tool("moderate_tool", {"path": "/test"})

            assert result.success is True

    def test_execute_moderate_safety_tool_cancelled(self, repl):
        """Test executing moderate safety tool when cancelled."""
        moderate_tool = Mock()
        moderate_tool.name = "moderate_tool"
        moderate_tool.safety = ToolSafety.MODERATE
        repl.tools["moderate_tool"] = moderate_tool

        with patch.object(repl, '_confirm_tool', return_value=False):
            result = repl._execute_tool("moderate_tool", {})

            assert result.success is False
            assert "cancelled" in result.output.lower()


class TestPaperGenREPLConfirmation:
    """Tests for tool confirmation."""

    def test_confirm_tool_yes(self):
        """Test confirming tool with 'y'."""
        repl = PaperGenREPL()

        with patch('builtins.input', return_value='y'):
            with patch.object(repl.console, 'print'):
                result = repl._confirm_tool("test", {"arg": "val"})

                assert result is True

    def test_confirm_tool_no(self):
        """Test confirming tool with 'n'."""
        repl = PaperGenREPL()

        with patch('builtins.input', return_value='n'):
            with patch.object(repl.console, 'print'):
                result = repl._confirm_tool("test", {})

                assert result is False


class TestPaperGenREPLCommands:
    """Tests for slash commands."""

    @pytest.fixture
    def repl(self):
        """Create REPL instance."""
        return PaperGenREPL()

    def test_handle_help_command(self, repl):
        """Test /help command."""
        with patch.object(repl, '_show_help') as mock_help:
            result = repl._handle_command("/help")

            assert result is True
            mock_help.assert_called_once()

    def test_handle_clear_command(self, repl):
        """Test /clear command."""
        with patch.object(repl.console, 'print'):
            with patch.object(repl.session, 'clear'):
                result = repl._handle_command("/clear")

                assert result is True

    def test_handle_exit_command(self, repl):
        """Test /exit command."""
        repl.running = True
        result = repl._handle_command("/exit")

        assert result is True
        assert repl.running is False

    def test_handle_quit_command(self, repl):
        """Test /quit command."""
        repl.running = True
        result = repl._handle_command("/quit")

        assert result is True
        assert repl.running is False

    def test_handle_unknown_command(self, repl):
        """Test unknown command."""
        result = repl._handle_command("/unknown")

        assert result is False


class TestPaperGenREPLSystemPrompt:
    """Tests for system prompt."""

    def test_get_system_prompt(self):
        """Test system prompt generation."""
        repl = PaperGenREPL()
        prompt = repl._get_system_prompt()

        assert "PaperGen" in prompt
        assert "research" in prompt.lower()


class TestPaperGenREPLHelp:
    """Tests for help display."""

    def test_show_help(self):
        """Test showing help."""
        repl = PaperGenREPL()

        with patch.object(repl.console, 'print') as mock_print:
            repl._show_help()

            mock_print.assert_called_once()
            help_text = mock_print.call_args[0][0]
            assert "/help" in help_text
            assert "/exit" in help_text


class TestPaperGenREPLChat:
    """Tests for chat functionality."""

    def test_chat_adds_message(self):
        """Test that chat adds message to session."""
        repl = PaperGenREPL()
        repl.session = Mock()

        mock_client = Mock()
        mock_client.stream_generate.return_value = iter(["Hello"])

        with patch('papergen.ai.claude_client.ClaudeClient', return_value=mock_client):
            with patch.object(repl.console, 'print'):
                repl._chat("Hello")

                repl.session.add_message.assert_called()

    def test_chat_handles_error(self):
        """Test that chat handles errors."""
        repl = PaperGenREPL()

        with patch('papergen.ai.claude_client.ClaudeClient') as mock_client:
            mock_client.side_effect = Exception("API Error")

            with patch.object(repl.console, 'print') as mock_print:
                repl._chat("Hello")

                # Should print error
                assert any("error" in str(call).lower() for call in mock_print.call_args_list)


class TestPaperGenREPLRun:
    """Tests for run loop."""

    def test_run_initializes(self):
        """Test that run initializes properly."""
        repl = PaperGenREPL()

        with patch.object(repl, '_load_default_tools'):
            with patch.object(repl.input_handler, 'initialize'):
                with patch.object(repl.input_handler, 'prompt', side_effect=["/exit"]):
                    with patch.object(repl.console, 'print'):
                        repl.run()

                        repl.input_handler.initialize.assert_called_once()

    def test_run_handles_empty_input(self):
        """Test that run handles empty input."""
        repl = PaperGenREPL()

        inputs = iter(["", "/exit"])

        with patch.object(repl, '_load_default_tools'):
            with patch.object(repl.input_handler, 'initialize'):
                with patch.object(repl.input_handler, 'prompt', side_effect=inputs):
                    with patch.object(repl.console, 'print'):
                        with patch.object(repl, '_chat') as mock_chat:
                            repl.run()

                            # Empty input should not trigger chat
                            mock_chat.assert_not_called()

    def test_run_handles_keyboard_interrupt(self):
        """Test that run handles KeyboardInterrupt."""
        repl = PaperGenREPL()

        with patch.object(repl, '_load_default_tools'):
            with patch.object(repl.input_handler, 'initialize'):
                with patch.object(repl.input_handler, 'prompt', side_effect=[KeyboardInterrupt, "/exit"]):
                    with patch.object(repl.console, 'print') as mock_print:
                        repl.run()

                        # Should print instruction to use /exit
                        assert any("/exit" in str(call) for call in mock_print.call_args_list)

    def test_run_handles_eof(self):
        """Test that run handles EOFError."""
        repl = PaperGenREPL()
        repl.running = True  # Start as running

        with patch.object(repl, '_load_default_tools'):
            with patch.object(repl.input_handler, 'initialize'):
                with patch.object(repl.input_handler, 'prompt', side_effect=EOFError):
                    with patch.object(repl.console, 'print'):
                        repl.run()

                        # Should have exited after EOFError
                        # running will be set to True initially, then exit via break
                        # This is expected behavior
