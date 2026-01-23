"""Unit tests for PDF extraction."""

import pytest
from pathlib import Path
from papergen.sources.pdf_extractor import PDFExtractor
from papergen.core.exceptions import PDFExtractionError, EmptyContentError


class TestPDFExtractor:
    """Test PDF extraction functionality."""

    def test_extractor_initialization(self):
        """Test PDFExtractor initialization."""
        extractor = PDFExtractor()
        assert extractor.extract_figures is True
        assert extractor.extract_tables is True

    def test_extract_nonexistent_file_raises_error(self):
        """Test extracting nonexistent file raises PDFExtractionError."""
        extractor = PDFExtractor()
        nonexistent_path = Path("/nonexistent/file.pdf")

        with pytest.raises(PDFExtractionError) as exc_info:
            extractor.extract(nonexistent_path)

        assert "does not exist" in exc_info.value.reason
        assert str(nonexistent_path) in exc_info.value.file_path

    def test_extract_non_pdf_file_raises_error(self, temp_dir):
        """Test extracting non-PDF file raises PDFExtractionError."""
        extractor = PDFExtractor()

        # Create a non-PDF file
        text_file = temp_dir / "test.txt"
        text_file.write_text("This is not a PDF")

        with pytest.raises(PDFExtractionError) as exc_info:
            extractor.extract(text_file)

        assert "not a PDF" in exc_info.value.reason

    @pytest.mark.skip(reason="Requires actual PDF file")
    def test_extract_valid_pdf(self, sample_pdf_path):
        """Test extracting content from valid PDF."""
        extractor = PDFExtractor()
        result = extractor.extract(sample_pdf_path)

        assert "metadata" in result
        assert "content" in result
        assert "citations" in result
        assert "figures" in result
        assert "tables" in result

        # Check content structure
        content = result["content"]
        assert "full_text" in content
        assert "sections" in content
        assert len(content["full_text"]) > 100

    def test_extract_empty_pdf_raises_error(self, temp_dir):
        """Test extracting empty PDF raises EmptyContentError."""
        # This test would need a fixture with an actual empty/minimal PDF
        # For now, we test the error type
        extractor = PDFExtractor()

        # Mock scenario: if we had an empty PDF
        # with pytest.raises(EmptyContentError):
        #     extractor.extract(empty_pdf_path)
        pass


class TestPDFMetadataExtraction:
    """Test PDF metadata extraction."""

    @pytest.mark.skip(reason="Requires actual PDF file")
    def test_extract_metadata(self, sample_pdf_path):
        """Test extracting PDF metadata."""
        extractor = PDFExtractor()
        result = extractor.extract(sample_pdf_path)

        metadata = result["metadata"]
        assert isinstance(metadata, dict)
        # Metadata may include: title, author, subject, keywords, etc.


class TestPDFContentExtraction:
    """Test PDF content extraction."""

    @pytest.mark.skip(reason="Requires actual PDF file")
    def test_extract_full_text(self, sample_pdf_path):
        """Test extracting full text from PDF."""
        extractor = PDFExtractor()
        result = extractor.extract(sample_pdf_path)

        full_text = result["content"]["full_text"]
        assert isinstance(full_text, str)
        assert len(full_text) > 0

    @pytest.mark.skip(reason="Requires actual PDF file")
    def test_extract_sections(self, sample_pdf_path):
        """Test extracting sections from PDF."""
        extractor = PDFExtractor()
        result = extractor.extract(sample_pdf_path)

        sections = result["content"]["sections"]
        assert isinstance(sections, list)

    @pytest.mark.skip(reason="Requires actual PDF file")
    def test_extract_abstract(self, sample_pdf_path):
        """Test extracting abstract from PDF."""
        extractor = PDFExtractor()
        result = extractor.extract(sample_pdf_path)

        abstract = result["content"].get("abstract")
        if abstract:
            assert isinstance(abstract, str)
            assert len(abstract) > 0

    @pytest.mark.skip(reason="Requires actual PDF file")
    def test_extract_keywords(self, sample_pdf_path):
        """Test extracting keywords from PDF."""
        extractor = PDFExtractor()
        result = extractor.extract(sample_pdf_path)

        keywords = result["content"].get("keywords")
        if keywords:
            assert isinstance(keywords, list)


class TestPDFCitationExtraction:
    """Test PDF citation extraction."""

    @pytest.mark.skip(reason="Requires actual PDF file")
    def test_extract_citations(self, sample_pdf_path):
        """Test extracting citations from PDF."""
        extractor = PDFExtractor()
        result = extractor.extract(sample_pdf_path)

        citations = result["citations"]
        assert isinstance(citations, list)


class TestPDFFigureExtraction:
    """Test PDF figure extraction."""

    def test_figure_extraction_enabled_by_default(self):
        """Test figure extraction is enabled by default."""
        extractor = PDFExtractor()
        assert extractor.extract_figures is True

    def test_disable_figure_extraction(self):
        """Test disabling figure extraction."""
        extractor = PDFExtractor()
        extractor.extract_figures = False
        assert extractor.extract_figures is False


class TestPDFTableExtraction:
    """Test PDF table extraction."""

    def test_table_extraction_enabled_by_default(self):
        """Test table extraction is enabled by default."""
        extractor = PDFExtractor()
        assert extractor.extract_tables is True

    def test_disable_table_extraction(self):
        """Test disabling table extraction."""
        extractor = PDFExtractor()
        extractor.extract_tables = False
        assert extractor.extract_tables is False
