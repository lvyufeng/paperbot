"""Tests for citation management."""

import pytest
from unittest.mock import Mock
from pathlib import Path
import tempfile
import json

from papergen.document.citation import Citation, CitationManager


class TestCitation:
    """Tests for Citation class."""

    def test_citation_creation(self):
        """Test creating a citation."""
        citation = Citation(
            key="smith2020",
            title="Test Paper",
            authors=["John Smith", "Jane Doe"],
            year="2020",
            journal="Test Journal",
            doi="10.1234/test"
        )

        assert citation.key == "smith2020"
        assert citation.title == "Test Paper"
        assert len(citation.authors) == 2
        assert citation.year == "2020"

    def test_citation_defaults(self):
        """Test citation default values."""
        citation = Citation(key="test")

        assert citation.title == ""
        assert citation.authors == []
        assert citation.year == ""
        assert citation.journal == ""

    def test_citation_extra_fields(self):
        """Test citation with extra fields."""
        citation = Citation(
            key="test",
            volume="10",
            pages="1-10",
            publisher="Test Publisher"
        )

        assert citation.extra["volume"] == "10"
        assert citation.extra["pages"] == "1-10"

    def test_citation_to_dict(self):
        """Test converting citation to dictionary."""
        citation = Citation(
            key="smith2020",
            title="Test Paper",
            authors=["John Smith"],
            year="2020",
            journal="Journal",
            doi="10.1234/test",
            url="https://example.com"
        )

        data = citation.to_dict()

        assert data["key"] == "smith2020"
        assert data["title"] == "Test Paper"
        assert data["authors"] == ["John Smith"]
        assert data["year"] == "2020"

    def test_citation_to_bibtex(self):
        """Test BibTeX export."""
        citation = Citation(
            key="smith2020",
            title="A Great Paper",
            authors=["John Smith", "Jane Doe"],
            year="2020",
            journal="Nature",
            doi="10.1234/paper"
        )

        bibtex = citation.to_bibtex()

        assert "@article{smith2020," in bibtex
        assert "title={A Great Paper}" in bibtex
        assert "author={John Smith and Jane Doe}" in bibtex
        assert "year={2020}" in bibtex
        assert "journal={Nature}" in bibtex

    def test_citation_to_bibtex_custom_type(self):
        """Test BibTeX with custom entry type."""
        citation = Citation(key="test", title="Proceedings Paper")
        bibtex = citation.to_bibtex(entry_type="inproceedings")

        assert "@inproceedings{test," in bibtex


class TestCitationManager:
    """Tests for CitationManager class."""

    def test_manager_creation(self):
        """Test creating a citation manager."""
        manager = CitationManager()
        assert manager.style == "apa"
        assert manager.citations == {}

    def test_manager_custom_style(self):
        """Test manager with custom style."""
        manager = CitationManager(style="ieee")
        assert manager.style == "ieee"

    def test_add_citation(self):
        """Test adding a citation."""
        manager = CitationManager()

        key = manager.add_citation(
            title="Test Paper",
            authors=["John Smith"],
            year="2020"
        )

        assert key == "smith2020"
        assert "smith2020" in manager.citations
        assert manager.citations[key].title == "Test Paper"

    def test_add_citation_generates_key(self):
        """Test key generation from author and year."""
        manager = CitationManager()

        key = manager.add_citation(
            title="Paper",
            authors=["John Smith"],
            year="2021"
        )
        assert key == "smith2021"

        key = manager.add_citation(
            title="Paper",
            authors=["Jane Doe-Williams"],
            year="2022"
        )
        assert "doe" in key.lower() or "williams" in key.lower()

    def test_add_citation_last_first_format(self):
        """Test key generation with 'Last, First' format."""
        manager = CitationManager()

        key = manager.add_citation(
            title="Paper",
            authors=["Smith, John"],
            year="2020"
        )
        assert key == "smith2020"

    def test_add_from_dict(self):
        """Test adding citation from dictionary."""
        manager = CitationManager()

        data = {
            "title": "Test Paper",
            "authors": ["John Smith"],
            "year": "2020",
            "journal": "Test Journal"
        }

        key = manager.add_from_dict(data)

        assert key in manager.citations
        assert manager.citations[key].journal == "Test Journal"

    def test_add_from_dict_with_key(self):
        """Test adding citation from dict with explicit key."""
        manager = CitationManager()

        data = {
            "key": "custom_key",
            "title": "Test"
        }

        key = manager.add_from_dict(data)
        assert key == "custom_key"

    def test_get_citation(self):
        """Test getting a citation by key."""
        manager = CitationManager()
        manager.add_citation(title="Test", authors=["Smith"], year="2020")

        citation = manager.get_citation("smith2020")
        assert citation is not None
        assert citation.title == "Test"

    def test_get_citation_not_found(self):
        """Test getting nonexistent citation."""
        manager = CitationManager()
        assert manager.get_citation("nonexistent") is None


class TestCitationManagerInlineFormatting:
    """Tests for inline citation formatting."""

    def test_format_inline_apa_single_author(self):
        """Test APA inline citation with single author."""
        manager = CitationManager(style="apa")
        manager.add_citation(title="Test", authors=["Smith, John"], year="2020")

        result = manager.format_inline("smith2020")
        # APA format uses last name from "Last, First" format
        assert "Smith" in result
        assert "2020" in result
        assert "(" in result and ")" in result

    def test_format_inline_apa_two_authors(self):
        """Test APA inline citation with two authors."""
        manager = CitationManager(style="apa")
        manager.add_citation(
            title="Test",
            authors=["John Smith", "Jane Doe"],
            year="2020"
        )

        result = manager.format_inline("smith2020")
        assert "&" in result or "and" in result.lower()

    def test_format_inline_apa_multiple_authors(self):
        """Test APA inline citation with multiple authors."""
        manager = CitationManager(style="apa")
        manager.add_citation(
            title="Test",
            authors=["A", "B", "C", "D"],
            year="2020"
        )

        result = manager.format_inline("a2020")
        assert "et al." in result

    def test_format_inline_ieee(self):
        """Test IEEE inline citation (numbered)."""
        manager = CitationManager(style="ieee")
        manager.add_citation(title="First", authors=["A"], year="2020")
        manager.add_citation(title="Second", authors=["B"], year="2021")

        result1 = manager.format_inline("a2020")
        result2 = manager.format_inline("b2021")

        assert "[1]" in result1
        assert "[2]" in result2

    def test_format_inline_unknown_key(self):
        """Test formatting with unknown citation key."""
        manager = CitationManager(style="apa")
        result = manager.format_inline("unknown")
        assert "[unknown]" in result


class TestCitationManagerBibliography:
    """Tests for bibliography generation."""

    def test_generate_bibliography_empty(self):
        """Test bibliography with no citations."""
        manager = CitationManager()
        result = manager.generate_bibliography()
        assert result == ""

    def test_generate_bibliography_apa(self):
        """Test APA bibliography generation."""
        manager = CitationManager(style="apa")
        manager.add_citation(
            title="Test Paper",
            authors=["Smith, John"],
            year="2020",
            journal="Nature"
        )

        result = manager.generate_bibliography()

        assert "# References" in result
        assert "Smith" in result
        assert "(2020)" in result
        assert "Test Paper" in result

    def test_generate_bibliography_ieee(self):
        """Test IEEE bibliography generation."""
        manager = CitationManager(style="ieee")
        manager.add_citation(
            title="First Paper",
            authors=["Smith, John"],
            year="2020"
        )
        manager.add_citation(
            title="Second Paper",
            authors=["Doe, Jane"],
            year="2021"
        )

        result = manager.generate_bibliography()

        assert "[1]" in result
        assert "[2]" in result

    def test_bibliography_apa_multiple_authors(self):
        """Test APA bibliography with multiple authors."""
        manager = CitationManager(style="apa")
        manager.add_citation(
            title="Team Paper",
            authors=["Smith, John", "Doe, Jane", "Brown, Bob"],
            year="2020"
        )

        result = manager.generate_bibliography()
        assert "&" in result  # APA uses & for last author


class TestCitationManagerExport:
    """Tests for export functionality."""

    def test_export_bibtex(self):
        """Test BibTeX export of all citations."""
        manager = CitationManager()
        manager.add_citation(title="Paper 1", authors=["Smith"], year="2020")
        manager.add_citation(title="Paper 2", authors=["Doe"], year="2021")

        bibtex = manager.export_bibtex()

        assert "@article{smith2020," in bibtex
        assert "@article{doe2021," in bibtex
        assert "Paper 1" in bibtex
        assert "Paper 2" in bibtex

    def test_save_and_load(self):
        """Test saving and loading citations."""
        manager = CitationManager(style="ieee")
        manager.add_citation(title="Test Paper", authors=["Smith"], year="2020")
        manager.add_citation(title="Another Paper", authors=["Doe"], year="2021")

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            path = Path(f.name)

        try:
            manager.save(path)

            # Load and verify
            loaded = CitationManager.load(path)

            assert loaded.style == "ieee"
            assert "smith2020" in loaded.citations
            assert "doe2021" in loaded.citations
            assert loaded.citations["smith2020"].title == "Test Paper"
        finally:
            path.unlink()


class TestCitationManagerTextProcessing:
    """Tests for text processing functionality."""

    def test_extract_citations_from_text(self):
        """Test extracting citation keys from text."""
        manager = CitationManager()

        text = "As shown by [CITE:smith2020], and confirmed by [CITE:doe2021]..."
        keys = manager.extract_citations_from_text(text)

        assert len(keys) == 2
        assert "smith2020" in keys
        assert "doe2021" in keys

    def test_extract_citations_empty(self):
        """Test extracting from text with no citations."""
        manager = CitationManager()

        text = "This text has no citations."
        keys = manager.extract_citations_from_text(text)

        assert keys == []

    def test_replace_citation_markers(self):
        """Test replacing citation markers."""
        manager = CitationManager(style="apa")
        manager.add_citation(title="Test", authors=["Smith"], year="2020")

        text = "As shown by [CITE:smith2020], the results..."
        result = manager.replace_citation_markers(text)

        assert "[CITE:" not in result
        assert "Smith" in result
        assert "2020" in result

    def test_replace_citation_markers_unknown(self):
        """Test replacing unknown citation markers."""
        manager = CitationManager()

        text = "See [CITE:unknown] for details."
        result = manager.replace_citation_markers(text)

        assert "[unknown]" in result


class TestCitationManagerKeyGeneration:
    """Tests for citation key generation."""

    def test_generate_key_standard(self):
        """Test standard key generation."""
        manager = CitationManager()

        key = manager._generate_key(["John Smith"], "2020")
        assert key == "smith2020"

    def test_generate_key_last_first_format(self):
        """Test key generation with 'Last, First' format."""
        manager = CitationManager()

        key = manager._generate_key(["Smith, John"], "2020")
        assert key == "smith2020"

    def test_generate_key_no_authors(self):
        """Test key generation without authors."""
        manager = CitationManager()

        key = manager._generate_key([], "2020")
        assert "ref2020" in key

    def test_generate_key_no_year(self):
        """Test key generation without year."""
        manager = CitationManager()
        manager.citation_counter = 5

        key = manager._generate_key([], "")
        assert "ref" in key

    def test_generate_key_special_characters(self):
        """Test key generation with special characters in name."""
        manager = CitationManager()

        key = manager._generate_key(["O'Brien, John"], "2020")
        # Should remove special characters
        assert "'" not in key
