"""Base tool interface for PaperGen CLI."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional
from enum import Enum


class ToolSafety(Enum):
    """Tool safety level for hybrid execution."""
    SAFE = "safe"        # Auto-execute (read-only)
    MODERATE = "moderate"  # Confirm for important ops
    DANGEROUS = "dangerous"  # Always confirm


@dataclass
class ToolResult:
    """Result from tool execution."""
    success: bool
    output: str
    error: Optional[str] = None
    data: Optional[Dict] = None


class BaseTool(ABC):
    """Base class for all tools."""

    name: str = "base_tool"
    description: str = "Base tool"
    safety: ToolSafety = ToolSafety.SAFE

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool."""
        pass

    def get_schema(self) -> Dict:
        """Get tool schema for API."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.get_input_schema()
        }

    @abstractmethod
    def get_input_schema(self) -> Dict:
        """Get input parameters schema."""
        pass
