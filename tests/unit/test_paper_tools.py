"""Tests for paper tools."""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import tempfile

from papergen.interactive.tools.paper_tools import AnalyzePDFTool, SearchPapersTool
from papergen.interactive.tools.base import ToolSafety


class TestAnalyzePDFTool:
    """Tests for AnalyzePDFTool."""

    @pytest.fixture
    def tool(self):
        """Create tool instance."""
        return AnalyzePDFTool()

    def test_tool_attributes(self, tool):
        """Test tool attributes."""
        assert tool.name == "analyze_pdf"
        assert tool.safety == ToolSafety.SAFE
        assert "pdf" in tool.description.lower()

    def test_get_input_schema(self, tool):
        """Test input schema."""
        schema = tool.get_input_schema()

        assert schema["type"] == "object"
        assert "path" in schema["properties"]
        assert "path" in schema["required"]

    def test_analyze_pdf_success(self, tool):
        """Test successful PDF analysis."""
        mock_extractor = Mock()
        mock_extractor.extract.return_value = {
            "full_text": "This is the paper content."
        }

        with patch('papergen.sources.pdf_extractor.PDFExtractor', return_value=mock_extractor):
            result = tool.execute(path="/path/to/paper.pdf")

            assert result.success is True
            assert "paper content" in result.output

    def test_analyze_pdf_truncates_long_content(self, tool):
        """Test that long content is truncated."""
        mock_extractor = Mock()
        mock_extractor.extract.return_value = {
            "full_text": "x" * 10000
        }

        with patch('papergen.sources.pdf_extractor.PDFExtractor', return_value=mock_extractor):
            result = tool.execute(path="/path/to/paper.pdf")

            assert result.success is True
            assert len(result.output) <= 5000

    def test_analyze_pdf_no_full_text(self, tool):
        """Test when no full_text in result."""
        mock_extractor = Mock()
        mock_extractor.extract.return_value = {
            "metadata": {"title": "Test"}
        }

        with patch('papergen.sources.pdf_extractor.PDFExtractor', return_value=mock_extractor):
            result = tool.execute(path="/path/to/paper.pdf")

            assert result.success is True
            assert result.output == ""

    def test_analyze_pdf_error(self, tool):
        """Test handling extraction errors."""
        with patch('papergen.sources.pdf_extractor.PDFExtractor') as mock_class:
            mock_class.return_value.extract.side_effect = Exception("PDF Error")

            result = tool.execute(path="/path/to/paper.pdf")

            assert result.success is False
            assert "PDF Error" in result.error


class TestSearchPapersTool:
    """Tests for SearchPapersTool."""

    @pytest.fixture
    def tool(self):
        """Create tool instance."""
        return SearchPapersTool()

    def test_tool_attributes(self, tool):
        """Test tool attributes."""
        assert tool.name == "search_papers"
        assert tool.safety == ToolSafety.SAFE
        assert "search" in tool.description.lower()

    def test_get_input_schema(self, tool):
        """Test input schema."""
        schema = tool.get_input_schema()

        assert schema["type"] == "object"
        assert "query" in schema["properties"]
        assert "limit" in schema["properties"]
        assert "min_citations" in schema["properties"]
        assert "query" in schema["required"]

    def test_search_papers_success(self, tool):
        """Test successful paper search."""
        mock_paper = Mock()
        mock_paper.title = "Test Paper"
        mock_paper.year = 2024
        mock_paper.authors = [{"name": "John Smith"}]
        mock_paper.citation_count = 100
        mock_paper.venue = "NeurIPS"
        mock_paper.paper_id = "abc123"

        mock_client = Mock()
        mock_client.search_papers.return_value = [mock_paper]

        with patch('papergen.sources.semantic_scholar.SemanticScholarClient', return_value=mock_client):
            result = tool.execute(query="machine learning")

            assert result.success is True
            assert "Test Paper" in result.output
            assert "2024" in result.output
            assert "John Smith" in result.output

    def test_search_papers_no_results(self, tool):
        """Test search with no results."""
        mock_client = Mock()
        mock_client.search_papers.return_value = []

        with patch('papergen.sources.semantic_scholar.SemanticScholarClient', return_value=mock_client):
            result = tool.execute(query="nonexistent topic xyz")

            assert result.success is True
            assert "no papers" in result.output.lower()

    def test_search_papers_with_limit(self, tool):
        """Test search with custom limit."""
        mock_client = Mock()
        mock_client.search_papers.return_value = []

        with patch('papergen.sources.semantic_scholar.SemanticScholarClient', return_value=mock_client):
            tool.execute(query="test", limit=10)

            mock_client.search_papers.assert_called_once()
            call_kwargs = mock_client.search_papers.call_args.kwargs
            assert call_kwargs["limit"] == 10

    def test_search_papers_with_min_citations(self, tool):
        """Test search with minimum citations filter."""
        mock_client = Mock()
        mock_client.search_papers.return_value = []

        with patch('papergen.sources.semantic_scholar.SemanticScholarClient', return_value=mock_client):
            tool.execute(query="test", min_citations=50)

            mock_client.search_papers.assert_called_once()
            call_kwargs = mock_client.search_papers.call_args.kwargs
            assert call_kwargs["min_citation_count"] == 50

    def test_search_papers_multiple_authors(self, tool):
        """Test formatting with multiple authors."""
        mock_paper = Mock()
        mock_paper.title = "Multi-Author Paper"
        mock_paper.year = 2024
        mock_paper.authors = [
            {"name": "Author 1"},
            {"name": "Author 2"},
            {"name": "Author 3"},
            {"name": "Author 4"},
            {"name": "Author 5"}
        ]
        mock_paper.citation_count = 50
        mock_paper.venue = "ICML"
        mock_paper.paper_id = "xyz789"

        mock_client = Mock()
        mock_client.search_papers.return_value = [mock_paper]

        with patch('papergen.sources.semantic_scholar.SemanticScholarClient', return_value=mock_client):
            result = tool.execute(query="test")

            assert result.success is True
            assert "et al." in result.output
            # First 3 authors should be shown
            assert "Author 1" in result.output
            assert "Author 2" in result.output
            assert "Author 3" in result.output

    def test_search_papers_no_venue(self, tool):
        """Test formatting when venue is None."""
        mock_paper = Mock()
        mock_paper.title = "Paper Without Venue"
        mock_paper.year = 2024
        mock_paper.authors = [{"name": "Author"}]
        mock_paper.citation_count = 10
        mock_paper.venue = None
        mock_paper.paper_id = "123"

        mock_client = Mock()
        mock_client.search_papers.return_value = [mock_paper]

        with patch('papergen.sources.semantic_scholar.SemanticScholarClient', return_value=mock_client):
            result = tool.execute(query="test")

            assert result.success is True
            assert "N/A" in result.output

    def test_search_papers_error(self, tool):
        """Test handling search errors."""
        with patch('papergen.sources.semantic_scholar.SemanticScholarClient') as mock_class:
            mock_class.return_value.search_papers.side_effect = Exception("API Error")

            result = tool.execute(query="test")

            assert result.success is False
            assert "API Error" in result.error


class TestToolSchemas:
    """Tests for tool schemas."""

    def test_analyze_pdf_schema_complete(self):
        """Test AnalyzePDFTool schema is complete."""
        tool = AnalyzePDFTool()
        schema = tool.get_schema()

        assert "name" in schema
        assert schema["name"] == "analyze_pdf"
        assert "description" in schema

    def test_search_papers_schema_complete(self):
        """Test SearchPapersTool schema is complete."""
        tool = SearchPapersTool()
        schema = tool.get_schema()

        assert "name" in schema
        assert schema["name"] == "search_papers"
        assert "description" in schema
