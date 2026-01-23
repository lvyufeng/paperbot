"""Tests for file tools."""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import tempfile

from papergen.interactive.tools.file_tools import (
    ReadFileTool, WriteFileTool, SearchFilesTool
)
from papergen.interactive.tools.base import ToolSafety


class TestReadFileTool:
    """Tests for ReadFileTool."""

    @pytest.fixture
    def tool(self):
        """Create tool instance."""
        return ReadFileTool()

    def test_tool_attributes(self, tool):
        """Test tool attributes."""
        assert tool.name == "read_file"
        assert tool.safety == ToolSafety.SAFE
        assert "read" in tool.description.lower()

    def test_get_input_schema(self, tool):
        """Test input schema."""
        schema = tool.get_input_schema()

        assert schema["type"] == "object"
        assert "path" in schema["properties"]
        assert "path" in schema["required"]

    def test_read_existing_file(self, tool):
        """Test reading an existing file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test content")
            temp_path = f.name

        try:
            result = tool.execute(path=temp_path)

            assert result.success is True
            assert result.output == "Test content"
        finally:
            Path(temp_path).unlink()

    def test_read_nonexistent_file(self, tool):
        """Test reading a nonexistent file."""
        result = tool.execute(path="/nonexistent/file.txt")

        assert result.success is False
        assert "not found" in result.error.lower()

    def test_read_file_with_error(self, tool):
        """Test handling read errors."""
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.read_text', side_effect=PermissionError("Access denied")):
                result = tool.execute(path="/some/file.txt")

                assert result.success is False
                assert result.error != ""


class TestWriteFileTool:
    """Tests for WriteFileTool."""

    @pytest.fixture
    def tool(self):
        """Create tool instance."""
        return WriteFileTool()

    def test_tool_attributes(self, tool):
        """Test tool attributes."""
        assert tool.name == "write_file"
        assert tool.safety == ToolSafety.MODERATE
        assert "write" in tool.description.lower()

    def test_get_input_schema(self, tool):
        """Test input schema."""
        schema = tool.get_input_schema()

        assert schema["type"] == "object"
        assert "path" in schema["properties"]
        assert "content" in schema["properties"]
        assert "path" in schema["required"]
        assert "content" in schema["required"]

    def test_write_new_file(self, tool):
        """Test writing a new file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "new_file.txt"

            result = tool.execute(path=str(file_path), content="Test content")

            assert result.success is True
            assert file_path.exists()
            assert file_path.read_text() == "Test content"

    def test_write_creates_directories(self, tool):
        """Test that writing creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "nested" / "dir" / "file.txt"

            result = tool.execute(path=str(file_path), content="Content")

            assert result.success is True
            assert file_path.exists()

    def test_write_overwrites_existing(self, tool):
        """Test overwriting existing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "existing.txt"
            file_path.write_text("Original")

            result = tool.execute(path=str(file_path), content="New content")

            assert result.success is True
            assert file_path.read_text() == "New content"

    def test_write_with_error(self, tool):
        """Test handling write errors."""
        with patch('pathlib.Path.write_text', side_effect=PermissionError("Access denied")):
            with patch('pathlib.Path.mkdir'):
                result = tool.execute(path="/some/file.txt", content="Content")

                assert result.success is False


class TestSearchFilesTool:
    """Tests for SearchFilesTool."""

    @pytest.fixture
    def tool(self):
        """Create tool instance."""
        return SearchFilesTool()

    def test_tool_attributes(self, tool):
        """Test tool attributes."""
        assert tool.name == "search_files"
        assert tool.safety == ToolSafety.SAFE
        assert "search" in tool.description.lower()

    def test_get_input_schema(self, tool):
        """Test input schema."""
        schema = tool.get_input_schema()

        assert schema["type"] == "object"
        assert "pattern" in schema["properties"]
        assert "path" in schema["properties"]
        assert "pattern" in schema["required"]

    def test_search_finds_files(self, tool):
        """Test searching finds matching files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            (Path(tmpdir) / "test1.txt").touch()
            (Path(tmpdir) / "test2.txt").touch()
            (Path(tmpdir) / "other.md").touch()

            result = tool.execute(pattern="*.txt", path=tmpdir)

            assert result.success is True
            assert "test1.txt" in result.output
            assert "test2.txt" in result.output
            assert "other.md" not in result.output

    def test_search_no_matches(self, tool):
        """Test searching with no matches."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = tool.execute(pattern="*.xyz", path=tmpdir)

            assert result.success is True
            assert "no files" in result.output.lower()

    def test_search_default_path(self, tool):
        """Test searching with default path."""
        result = tool.execute(pattern="*.nonexistent_extension_xyz")

        assert result.success is True

    def test_search_limits_results(self, tool):
        """Test that search limits results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create many files
            for i in range(100):
                (Path(tmpdir) / f"file{i}.txt").touch()

            result = tool.execute(pattern="*.txt", path=tmpdir)

            assert result.success is True
            # Should be limited to 50 files
            assert result.output.count("\n") <= 50

    def test_search_with_error(self, tool):
        """Test handling search errors."""
        with patch('pathlib.Path.glob', side_effect=PermissionError("Access denied")):
            result = tool.execute(pattern="*.txt", path="/some/path")

            assert result.success is False


class TestToolSchemas:
    """Tests for tool schemas used by AI."""

    def test_read_file_schema_complete(self):
        """Test ReadFileTool schema is complete."""
        tool = ReadFileTool()
        schema = tool.get_schema()

        assert "name" in schema
        assert "description" in schema
        assert "input_schema" in schema or "parameters" in schema

    def test_write_file_schema_complete(self):
        """Test WriteFileTool schema is complete."""
        tool = WriteFileTool()
        schema = tool.get_schema()

        assert "name" in schema
        assert "description" in schema

    def test_search_files_schema_complete(self):
        """Test SearchFilesTool schema is complete."""
        tool = SearchFilesTool()
        schema = tool.get_schema()

        assert "name" in schema
        assert "description" in schema
