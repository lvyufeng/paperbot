"""Tests for Session and Message classes."""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from datetime import datetime
import tempfile
import json

from papergen.interactive.session import Session, Message


class TestMessage:
    """Tests for Message dataclass."""

    def test_create_message(self):
        """Test creating a message."""
        msg = Message(role="user", content="Hello")

        assert msg.role == "user"
        assert msg.content == "Hello"
        assert isinstance(msg.timestamp, datetime)
        assert msg.tool_calls == []
        assert msg.tool_results == []

    def test_create_message_with_tools(self):
        """Test creating message with tool calls."""
        msg = Message(
            role="assistant",
            content="Response",
            tool_calls=[{"name": "test_tool"}],
            tool_results=[{"result": "success"}]
        )

        assert msg.role == "assistant"
        assert len(msg.tool_calls) == 1
        assert len(msg.tool_results) == 1

    def test_message_to_dict(self):
        """Test converting message to dict."""
        msg = Message(role="user", content="Test")

        result = msg.to_dict()

        assert result["role"] == "user"
        assert result["content"] == "Test"
        assert "timestamp" in result
        assert result["tool_calls"] == []
        assert result["tool_results"] == []


class TestSessionInit:
    """Tests for Session initialization."""

    def test_init_default_id(self):
        """Test init with default session ID."""
        session = Session()

        assert session.session_id is not None
        assert len(session.session_id) == 8
        assert session.messages == []
        assert isinstance(session.created_at, datetime)

    def test_init_custom_id(self):
        """Test init with custom session ID."""
        session = Session(session_id="custom123")

        assert session.session_id == "custom123"


class TestSessionAddMessage:
    """Tests for add_message method."""

    def test_add_user_message(self):
        """Test adding user message."""
        session = Session()

        msg = session.add_message("user", "Hello")

        assert len(session.messages) == 1
        assert session.messages[0].role == "user"
        assert session.messages[0].content == "Hello"
        assert msg.role == "user"

    def test_add_assistant_message(self):
        """Test adding assistant message."""
        session = Session()

        session.add_message("assistant", "Hi there!")

        assert len(session.messages) == 1
        assert session.messages[0].role == "assistant"

    def test_add_multiple_messages(self):
        """Test adding multiple messages."""
        session = Session()

        session.add_message("user", "Hello")
        session.add_message("assistant", "Hi!")
        session.add_message("user", "How are you?")

        assert len(session.messages) == 3

    def test_add_message_with_kwargs(self):
        """Test adding message with additional kwargs."""
        session = Session()

        session.add_message(
            "assistant",
            "Response",
            tool_calls=[{"name": "test"}]
        )

        assert len(session.messages[0].tool_calls) == 1


class TestSessionGetMessagesForAPI:
    """Tests for get_messages_for_api method."""

    def test_get_messages_empty(self):
        """Test get messages when empty."""
        session = Session()

        result = session.get_messages_for_api()

        assert result == []

    def test_get_messages_single(self):
        """Test get messages with single message."""
        session = Session()
        session.add_message("user", "Hello")

        result = session.get_messages_for_api()

        assert len(result) == 1
        assert result[0] == {"role": "user", "content": "Hello"}

    def test_get_messages_multiple(self):
        """Test get messages with multiple messages."""
        session = Session()
        session.add_message("user", "Hello")
        session.add_message("assistant", "Hi!")

        result = session.get_messages_for_api()

        assert len(result) == 2
        assert result[0]["role"] == "user"
        assert result[1]["role"] == "assistant"


class TestSessionClear:
    """Tests for clear method."""

    def test_clear_messages(self):
        """Test clearing messages."""
        session = Session()
        session.add_message("user", "Message 1")
        session.add_message("assistant", "Message 2")

        session.clear()

        assert session.messages == []


class TestSessionSave:
    """Tests for save method."""

    def test_save_session(self):
        """Test saving session to file."""
        session = Session(session_id="test123")
        session.add_message("user", "Hello")
        session.add_message("assistant", "Hi!")

        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = Path(tmpdir) / "session.json"

            session.save(save_path)

            assert save_path.exists()

            with open(save_path) as f:
                data = json.load(f)

            assert data["session_id"] == "test123"
            assert len(data["messages"]) == 2


class TestSessionLoad:
    """Tests for load class method."""

    def test_load_session(self):
        """Test loading session from file."""
        session_data = {
            "session_id": "loaded123",
            "created_at": datetime.now().isoformat(),
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi!"}
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            load_path = Path(tmpdir) / "session.json"
            with open(load_path, 'w') as f:
                json.dump(session_data, f)

            session = Session.load(load_path)

            assert session.session_id == "loaded123"
            assert len(session.messages) == 2
            assert session.messages[0].role == "user"
            assert session.messages[1].role == "assistant"


class TestSessionContext:
    """Tests for session context."""

    def test_context_initially_empty(self):
        """Test context is initially empty."""
        session = Session()

        assert session.context == {}

    def test_context_can_be_modified(self):
        """Test context can be modified."""
        session = Session()

        session.context["topic"] = "Machine Learning"
        session.context["project_path"] = "/path/to/project"

        assert session.context["topic"] == "Machine Learning"
        assert session.context["project_path"] == "/path/to/project"


class TestSessionWorkingDir:
    """Tests for working directory."""

    def test_working_dir_default(self):
        """Test working dir defaults to cwd."""
        session = Session()

        assert session.working_dir == Path.cwd()
