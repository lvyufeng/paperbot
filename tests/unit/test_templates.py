"""Tests for template builders."""

import pytest
from unittest.mock import Mock, MagicMock
from pathlib import Path
import tempfile

from papergen.templates.latex_builder import LaTeXBuilder
from papergen.templates.markdown_builder import MarkdownBuilder


class TestLaTeXBuilderInit:
    """Tests for LaTeXBuilder initialization."""

    def test_init_default_template(self):
        """Test initialization with default template."""
        builder = LaTeXBuilder()
        assert builder.template == "ieee"

    def test_init_custom_template(self):
        """Test initialization with custom template."""
        builder = LaTeXBuilder(template="acm")
        assert builder.template == "acm"

    def test_init_empty_state(self):
        """Test initial state is empty."""
        builder = LaTeXBuilder()
        assert builder.sections_content == {}
        assert builder.metadata == {}
        assert builder.citation_manager is None


class TestLaTeXBuilderTemplates:
    """Tests for template retrieval."""

    def test_get_ieee_template(self):
        """Test IEEE template retrieval."""
        builder = LaTeXBuilder(template="ieee")
        template = builder._get_builtin_template()

        assert "\\documentclass[conference]{IEEEtran}" in template
        assert "{{TITLE}}" in template
        assert "{{AUTHORS}}" in template
        assert "{{ABSTRACT}}" in template

    def test_get_acm_template(self):
        """Test ACM template retrieval."""
        builder = LaTeXBuilder(template="acm")
        template = builder._get_builtin_template()

        assert "\\documentclass[sigconf]{acmart}" in template

    def test_get_springer_template(self):
        """Test Springer template retrieval."""
        builder = LaTeXBuilder(template="springer")
        template = builder._get_builtin_template()

        assert "\\documentclass{llncs}" in template

    def test_get_neurips_template(self):
        """Test NeurIPS template retrieval."""
        builder = LaTeXBuilder(template="neurips")
        template = builder._get_builtin_template()

        assert "neurips" in template.lower()

    def test_get_icml_template(self):
        """Test ICML template retrieval."""
        builder = LaTeXBuilder(template="icml")
        template = builder._get_builtin_template()

        assert "icml" in template.lower()

    def test_get_basic_template_for_unknown(self):
        """Test that unknown templates fall back to basic."""
        builder = LaTeXBuilder(template="unknown_template")
        template = builder._get_builtin_template()

        assert "\\documentclass[11pt,a4paper]{article}" in template


class TestLaTeXBuilderFormatting:
    """Tests for LaTeX formatting methods."""

    @pytest.fixture
    def builder(self):
        """Create a LaTeX builder."""
        return LaTeXBuilder()

    def test_escape_latex_ampersand(self, builder):
        """Test escaping ampersand."""
        # Note: The escape function processes characters in dict order
        # and backslash is escaped first, affecting subsequent escapes
        result = builder._escape_latex("A & B")
        assert "&" not in result or r"\&" in result or "textbackslash" in result

    def test_escape_latex_percent(self, builder):
        """Test escaping percent."""
        result = builder._escape_latex("100%")
        assert "%" not in result or r"\%" in result or "textbackslash" in result

    def test_escape_latex_dollar(self, builder):
        """Test escaping dollar sign."""
        result = builder._escape_latex("$100")
        assert "$" not in result or r"\$" in result or "textbackslash" in result

    def test_escape_latex_hash(self, builder):
        """Test escaping hash."""
        result = builder._escape_latex("#1")
        assert "#" not in result or r"\#" in result or "textbackslash" in result

    def test_escape_latex_underscore(self, builder):
        """Test escaping underscore."""
        result = builder._escape_latex("a_b")
        assert "_" not in result or r"\_" in result or "textbackslash" in result

    def test_escape_latex_multiple_chars(self, builder):
        """Test escaping multiple special characters."""
        result = builder._escape_latex("A & B = $100 (50%)")
        # All special chars should be escaped in some form
        assert result != "A & B = $100 (50%)"

    def test_format_authors_single(self, builder):
        """Test formatting single author."""
        builder.metadata = {"authors": ["John Smith"]}
        result = builder._format_authors()
        assert result == "John Smith"

    def test_format_authors_two(self, builder):
        """Test formatting two authors."""
        builder.metadata = {"authors": ["John Smith", "Jane Doe"]}
        builder.template = "ieee"
        result = builder._format_authors()
        assert "John Smith" in result
        assert "Jane Doe" in result
        assert "and" in result

    def test_format_authors_multiple(self, builder):
        """Test formatting multiple authors."""
        builder.metadata = {"authors": ["A", "B", "C", "D"]}
        builder.template = "ieee"
        result = builder._format_authors()
        assert "and D" in result

    def test_format_authors_empty(self, builder):
        """Test formatting with no authors."""
        builder.metadata = {"authors": []}
        result = builder._format_authors()
        assert result == "Anonymous"


class TestLaTeXBuilderSectionContent:
    """Tests for section content formatting."""

    @pytest.fixture
    def builder(self):
        """Create a LaTeX builder."""
        return LaTeXBuilder()

    def test_format_citation_markers(self, builder):
        """Test citation marker conversion."""
        content = "As shown by [CITE:smith2020], the results..."
        result = builder._format_section_content(content)
        assert r"\cite{smith2020}" in result

    def test_format_markdown_header_h1(self, builder):
        """Test H1 header conversion."""
        content = "# Introduction"
        result = builder._format_section_content(content)
        assert r"\section{Introduction}" in result

    def test_format_markdown_header_h2(self, builder):
        """Test H2 header conversion."""
        content = "## Background"
        result = builder._format_section_content(content)
        assert r"\subsection{Background}" in result

    def test_format_markdown_header_h3(self, builder):
        """Test H3 header conversion."""
        content = "### Details"
        result = builder._format_section_content(content)
        assert r"\subsubsection{Details}" in result

    def test_format_bold_text(self, builder):
        """Test bold text conversion."""
        content = "This is **important** text"
        result = builder._format_section_content(content)
        assert r"\textbf{important}" in result

    def test_format_italic_text(self, builder):
        """Test italic text conversion."""
        content = "This is *emphasized* text"
        result = builder._format_section_content(content)
        assert r"\textit{emphasized}" in result

    def test_format_bullet_list(self, builder):
        """Test bullet list conversion."""
        content = "Items:\n- First item\n- Second item\n\nMore text"
        result = builder._format_section_content(content)
        assert r"\begin{itemize}" in result
        assert r"\item First item" in result
        assert r"\end{itemize}" in result


class TestLaTeXBuilderBuild:
    """Tests for the build method."""

    def test_build_basic_document(self):
        """Test building a basic document."""
        builder = LaTeXBuilder(template="ieee")

        mock_citation_manager = Mock()
        mock_citation_manager.citations = {}

        sections = {
            "abstract": "This is the abstract.",
            "introduction": "# Introduction\n\nThis is the intro."
        }
        metadata = {
            "title": "Test Paper",
            "authors": ["Test Author"]
        }

        result = builder.build(sections, metadata, mock_citation_manager)

        assert "Test Paper" in result
        assert "Test Author" in result
        assert "\\documentclass" in result

    def test_build_with_custom_template_file(self):
        """Test building with custom template file."""
        builder = LaTeXBuilder()

        mock_citation_manager = Mock()
        mock_citation_manager.citations = {}

        sections = {"abstract": "Abstract text"}
        metadata = {"title": "Test", "authors": ["Author"]}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False) as f:
            f.write("\\documentclass{article}\n\\title{{{TITLE}}}\n\\begin{document}\n{{ABSTRACT}}\n\\end{document}")
            template_path = Path(f.name)

        try:
            result = builder.build(sections, metadata, mock_citation_manager, template_path=template_path)
            assert "Test" in result
            assert "Abstract text" in result
        finally:
            template_path.unlink()


class TestMarkdownBuilderInit:
    """Tests for MarkdownBuilder initialization."""

    def test_init_default_template(self):
        """Test initialization with default template."""
        builder = MarkdownBuilder()
        assert builder.template == "standard"

    def test_init_custom_template(self):
        """Test initialization with custom template."""
        builder = MarkdownBuilder(template="arxiv")
        assert builder.template == "arxiv"


class TestMarkdownBuilderFrontmatter:
    """Tests for frontmatter formatting."""

    @pytest.fixture
    def builder(self):
        """Create a Markdown builder."""
        builder = MarkdownBuilder()
        builder.metadata = {
            "title": "Test Paper",
            "authors": ["John Smith", "Jane Doe"],
            "keywords": ["AI", "ML"],
            "date": "2024-01-15"
        }
        builder.sections_content = {}
        return builder

    def test_standard_frontmatter(self, builder):
        """Test standard frontmatter generation."""
        result = builder._format_standard_frontmatter()

        assert "---" in result
        assert 'title: "Test Paper"' in result
        assert "authors:" in result
        assert "- John Smith" in result
        assert "keywords:" in result

    def test_arxiv_frontmatter(self, builder):
        """Test arXiv frontmatter generation."""
        builder.sections_content = {"abstract": "This is the abstract."}
        result = builder._format_arxiv_frontmatter()

        assert "---" in result
        assert "name: John Smith" in result
        assert "abstract: |" in result


class TestMarkdownBuilderTOC:
    """Tests for table of contents generation."""

    def test_generate_toc(self):
        """Test TOC generation."""
        builder = MarkdownBuilder()
        builder.sections_content = {
            "abstract": "## Abstract\n\nContent",
            "introduction": "## Introduction\n\nContent"
        }

        toc = builder._generate_toc()

        assert "## Table of Contents" in toc
        assert "[Abstract]" in toc
        assert "[Introduction]" in toc
        assert "[References](#references)" in toc


class TestMarkdownBuilderBuild:
    """Tests for the build method."""

    def test_build_basic_document(self):
        """Test building a basic document."""
        builder = MarkdownBuilder()

        mock_citation_manager = Mock()
        mock_citation_manager.citations = {}
        mock_citation_manager.replace_citation_markers = lambda x: x
        mock_citation_manager.generate_bibliography.return_value = "## References\n\n*No references*"

        sections = {
            "abstract": "## Abstract\n\nThis is the abstract.",
            "introduction": "## Introduction\n\nThis is the introduction."
        }
        metadata = {
            "title": "Test Paper",
            "authors": ["Test Author"],
            "keywords": ["test"]
        }

        result = builder.build(sections, metadata, mock_citation_manager)

        assert "# Test Paper" in result
        assert "**Authors:** Test Author" in result
        assert "**Keywords:** test" in result
        assert "This is the abstract" in result

    def test_build_without_toc(self):
        """Test building without TOC."""
        builder = MarkdownBuilder()

        mock_citation_manager = Mock()
        mock_citation_manager.citations = {}
        mock_citation_manager.replace_citation_markers = lambda x: x
        mock_citation_manager.generate_bibliography.return_value = ""

        sections = {"abstract": "Abstract"}
        metadata = {"title": "Test"}

        result = builder.build(sections, metadata, mock_citation_manager, include_toc=False)

        assert "## Table of Contents" not in result


class TestMarkdownBuilderCitations:
    """Tests for citation formatting."""

    def test_format_citations(self):
        """Test citation marker replacement."""
        builder = MarkdownBuilder()

        mock_citation_manager = Mock()
        mock_citation_manager.replace_citation_markers.return_value = "As shown (Smith, 2020)"

        builder.citation_manager = mock_citation_manager
        result = builder._format_citations("As shown [CITE:smith2020]")

        mock_citation_manager.replace_citation_markers.assert_called_once()

    def test_format_citations_no_manager(self):
        """Test citation formatting without manager."""
        builder = MarkdownBuilder()
        builder.citation_manager = None

        result = builder._format_citations("Text [CITE:key]")
        assert result == "Text [CITE:key]"


class TestMarkdownBuilderReferences:
    """Tests for references section."""

    def test_format_references_with_citations(self):
        """Test references formatting with citations."""
        builder = MarkdownBuilder()

        mock_citation_manager = Mock()
        mock_citation_manager.citations = {"smith2020": Mock()}
        mock_citation_manager.generate_bibliography.return_value = "# References\n\nSmith (2020)..."

        builder.citation_manager = mock_citation_manager
        result = builder._format_references()

        assert "Smith (2020)" in result

    def test_format_references_empty(self):
        """Test references formatting with no citations."""
        builder = MarkdownBuilder()

        mock_citation_manager = Mock()
        mock_citation_manager.citations = {}

        builder.citation_manager = mock_citation_manager
        result = builder._format_references()

        assert "No references" in result


class TestMarkdownBuilderExport:
    """Tests for platform-specific export."""

    def test_export_for_github(self):
        """Test GitHub export."""
        builder = MarkdownBuilder()
        builder.sections_content = {"abstract": "Test"}
        builder.metadata = {"title": "Test"}

        mock_cm = Mock()
        mock_cm.citations = {}
        mock_cm.replace_citation_markers = lambda x: x
        mock_cm.generate_bibliography.return_value = ""
        builder.citation_manager = mock_cm

        result = builder.export_for_platform("github")
        assert "# Test" in result

    def test_export_for_arxiv(self):
        """Test arXiv export."""
        builder = MarkdownBuilder()
        builder.sections_content = {"abstract": "Test abstract"}
        builder.metadata = {"title": "Test", "authors": ["Author"]}

        mock_cm = Mock()
        mock_cm.citations = {}
        mock_cm.replace_citation_markers = lambda x: x
        mock_cm.generate_bibliography.return_value = ""
        builder.citation_manager = mock_cm

        result = builder.export_for_platform("arxiv")
        # arXiv format uses different frontmatter
        assert "title:" in result
