"""Tests for TextExtractor."""

import pytest
from pathlib import Path
import tempfile

from papergen.sources.text_extractor import TextExtractor


class TestTextExtractorBasic:
    """Tests for basic text extraction."""

    @pytest.fixture
    def extractor(self):
        """Create extractor instance."""
        return TextExtractor()

    def test_extract_plain_text(self, extractor):
        """Test extracting plain text file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is plain text content.\nWith multiple lines.")
            temp_path = Path(f.name)

        try:
            result = extractor.extract(temp_path)

            assert result["metadata"]["filename"] == temp_path.name
            assert result["metadata"]["file_type"] == ".txt"
            assert "plain text content" in result["content"]["full_text"]
            assert result["content"]["sections"] == []
        finally:
            temp_path.unlink()

    def test_extract_markdown_file(self, extractor):
        """Test extracting markdown file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Heading 1\nContent under heading 1.\n\n# Heading 2\nContent under heading 2.")
            temp_path = Path(f.name)

        try:
            result = extractor.extract(temp_path)

            assert result["metadata"]["file_type"] == ".md"
            assert len(result["content"]["sections"]) == 2
            assert result["content"]["sections"][0]["title"] == "Heading 1"
            assert result["content"]["sections"][1]["title"] == "Heading 2"
        finally:
            temp_path.unlink()

    def test_extract_empty_file(self, extractor):
        """Test extracting empty file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("")
            temp_path = Path(f.name)

        try:
            result = extractor.extract(temp_path)

            assert result["content"]["full_text"] == ""
            assert result["citations"] == []
            assert result["figures"] == []
            assert result["tables"] == []
        finally:
            temp_path.unlink()

    def test_extract_nonexistent_file(self, extractor):
        """Test extracting nonexistent file."""
        result = extractor.extract(Path("/nonexistent/file.txt"))

        assert "error" in result["metadata"]
        assert result["content"]["full_text"] == ""


class TestMarkdownSectionParsing:
    """Tests for markdown section parsing."""

    @pytest.fixture
    def extractor(self):
        """Create extractor instance."""
        return TextExtractor()

    def test_parse_single_section(self, extractor):
        """Test parsing single section."""
        text = "# Introduction\nThis is the intro content."
        sections = extractor._parse_markdown_sections(text)

        assert len(sections) == 1
        assert sections[0]["title"] == "Introduction"
        assert "intro content" in sections[0]["text"]

    def test_parse_multiple_sections(self, extractor):
        """Test parsing multiple sections."""
        text = """# Section 1
Content 1

# Section 2
Content 2

# Section 3
Content 3"""
        sections = extractor._parse_markdown_sections(text)

        assert len(sections) == 3
        assert sections[0]["title"] == "Section 1"
        assert sections[1]["title"] == "Section 2"
        assert sections[2]["title"] == "Section 3"

    def test_parse_nested_headers(self, extractor):
        """Test parsing nested headers."""
        text = """# Main Section
Main content

## Subsection
Sub content

### Sub-subsection
Deep content"""
        sections = extractor._parse_markdown_sections(text)

        # All headers are treated as sections
        assert len(sections) == 3
        assert sections[0]["title"] == "Main Section"
        assert sections[1]["title"] == "Subsection"
        assert sections[2]["title"] == "Sub-subsection"

    def test_parse_no_sections(self, extractor):
        """Test parsing text with no headers."""
        text = "Just plain text\nWith no headers."
        sections = extractor._parse_markdown_sections(text)

        assert len(sections) == 0

    def test_parse_empty_text(self, extractor):
        """Test parsing empty text."""
        sections = extractor._parse_markdown_sections("")

        assert sections == []

    def test_section_content_preserved(self, extractor):
        """Test that section content is preserved correctly."""
        text = """# Title
First paragraph.

Second paragraph with more text.

Third paragraph."""
        sections = extractor._parse_markdown_sections(text)

        assert "First paragraph" in sections[0]["text"]
        assert "Second paragraph" in sections[0]["text"]
        assert "Third paragraph" in sections[0]["text"]


class TestTextExtractorEdgeCases:
    """Tests for edge cases."""

    @pytest.fixture
    def extractor(self):
        """Create extractor instance."""
        return TextExtractor()

    def test_extract_unicode_content(self, extractor):
        """Test extracting file with unicode."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("Unicode: café, naïve, 日本語")
            temp_path = Path(f.name)

        try:
            result = extractor.extract(temp_path)

            assert "café" in result["content"]["full_text"]
            assert "日本語" in result["content"]["full_text"]
        finally:
            temp_path.unlink()

    def test_extract_large_file(self, extractor):
        """Test extracting large file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("x" * 100000)
            temp_path = Path(f.name)

        try:
            result = extractor.extract(temp_path)

            assert len(result["content"]["full_text"]) == 100000
        finally:
            temp_path.unlink()

    def test_markdown_extension_variations(self, extractor):
        """Test that .markdown extension is recognized."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.markdown', delete=False) as f:
            f.write("# Heading\nContent")
            temp_path = Path(f.name)

        try:
            result = extractor.extract(temp_path)

            # Should parse sections for .markdown files too
            assert len(result["content"]["sections"]) == 1
        finally:
            temp_path.unlink()
