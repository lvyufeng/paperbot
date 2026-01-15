"""File operation tools for PaperGen CLI."""

from pathlib import Path
from typing import Dict
from .base import BaseTool, ToolResult, ToolSafety


class ReadFileTool(BaseTool):
    """Read file contents."""

    name = "read_file"
    description = "Read contents of a file"
    safety = ToolSafety.SAFE

    def get_input_schema(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path"}
            },
            "required": ["path"]
        }

    def execute(self, path: str) -> ToolResult:
        try:
            p = Path(path)
            if not p.exists():
                return ToolResult(False, "", f"File not found: {path}")
            content = p.read_text()
            return ToolResult(True, content)
        except Exception as e:
            return ToolResult(False, "", str(e))


class WriteFileTool(BaseTool):
    """Write content to a file."""

    name = "write_file"
    description = "Write content to a file"
    safety = ToolSafety.MODERATE

    def get_input_schema(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path"},
                "content": {"type": "string", "description": "Content to write"}
            },
            "required": ["path", "content"]
        }

    def execute(self, path: str, content: str) -> ToolResult:
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content)
            return ToolResult(True, f"Written to {path}")
        except Exception as e:
            return ToolResult(False, "", str(e))


class SearchFilesTool(BaseTool):
    """Search for files by pattern."""

    name = "search_files"
    description = "Search for files matching a glob pattern"
    safety = ToolSafety.SAFE

    def get_input_schema(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Glob pattern"},
                "path": {"type": "string", "description": "Search directory"}
            },
            "required": ["pattern"]
        }

    def execute(self, pattern: str, path: str = ".") -> ToolResult:
        try:
            p = Path(path)
            files = list(p.glob(pattern))[:50]
            result = "\n".join(str(f) for f in files)
            return ToolResult(True, result or "No files found")
        except Exception as e:
            return ToolResult(False, "", str(e))
