"""Paper-specific tools for PaperGen CLI."""

from pathlib import Path
from typing import Dict
from .base import BaseTool, ToolResult, ToolSafety


class AnalyzePDFTool(BaseTool):
    """Analyze a PDF paper."""

    name = "analyze_pdf"
    description = "Extract and analyze content from a PDF paper"
    safety = ToolSafety.SAFE

    def get_input_schema(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "PDF file path"}
            },
            "required": ["path"]
        }

    def execute(self, path: str) -> ToolResult:
        try:
            from ...sources.pdf_extractor import PDFExtractor
            extractor = PDFExtractor()
            content = extractor.extract(Path(path))
            return ToolResult(True, content.get("full_text", "")[:5000])
        except Exception as e:
            return ToolResult(False, "", str(e))


class SearchPapersTool(BaseTool):
    """Search for academic papers."""

    name = "search_papers"
    description = "Search for papers on arXiv or Semantic Scholar"
    safety = ToolSafety.SAFE

    def get_input_schema(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "limit": {"type": "integer", "description": "Max results"}
            },
            "required": ["query"]
        }

    def execute(self, query: str, limit: int = 5) -> ToolResult:
        try:
            import requests
            url = f"https://api.semanticscholar.org/graph/v1/paper/search"
            params = {"query": query, "limit": limit, "fields": "title,year,authors"}
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            papers = data.get("data", [])
            result = "\n".join([f"- {p['title']} ({p.get('year', 'N/A')})" for p in papers])
            return ToolResult(True, result or "No papers found")
        except Exception as e:
            return ToolResult(False, "", str(e))
