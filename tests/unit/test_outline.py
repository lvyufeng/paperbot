"""Tests for outline management."""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import json
import tempfile

from papergen.document.outline import Section, Outline, OutlineGenerator


class TestSection:
    """Tests for Section model."""

    def test_section_creation(self):
        """Test basic section creation."""
        section = Section(
            id="intro",
            title="Introduction",
            level=1,
            order=1,
            word_count_target=1500
        )

        assert section.id == "intro"
        assert section.title == "Introduction"
        assert section.level == 1
        assert section.word_count_target == 1500

    def test_section_defaults(self):
        """Test section default values."""
        section = Section(id="test", title="Test")

        assert section.level == 1
        assert section.order == 0
        assert section.objectives == []
        assert section.key_points == []
        assert section.word_count_target == 1000
        assert section.sources == []
        assert section.subsections == []

    def test_section_with_subsections(self):
        """Test section with subsections."""
        subsection = Section(id="intro_bg", title="Background", level=2)
        section = Section(
            id="intro",
            title="Introduction",
            subsections=[subsection]
        )

        assert len(section.subsections) == 1
        assert section.subsections[0].id == "intro_bg"

    def test_section_to_markdown(self):
        """Test section markdown conversion."""
        section = Section(
            id="intro",
            title="Introduction",
            objectives=["Introduce topic", "State thesis"],
            key_points=["Background", "Motivation"],
            word_count_target=1500
        )

        markdown = section.to_markdown()

        assert "# Introduction" in markdown
        assert "**Objectives:**" in markdown
        assert "- Introduce topic" in markdown
        assert "**Key Points:**" in markdown
        assert "**Target:** 1500 words" in markdown

    def test_section_to_markdown_with_subsections(self):
        """Test section markdown with nested subsections."""
        subsection = Section(id="bg", title="Background", level=2)
        section = Section(
            id="intro",
            title="Introduction",
            subsections=[subsection]
        )

        markdown = section.to_markdown()

        assert "# Introduction" in markdown
        assert "## Background" in markdown

    def test_section_with_guidance(self):
        """Test section with guidance note."""
        section = Section(
            id="methods",
            title="Methods",
            guidance="Focus on reproducibility"
        )

        markdown = section.to_markdown()
        assert "**Note:** Focus on reproducibility" in markdown


class TestOutline:
    """Tests for Outline model."""

    @pytest.fixture
    def sample_outline(self):
        """Create a sample outline."""
        return Outline(
            topic="Machine Learning Research",
            sections=[
                Section(id="abstract", title="Abstract", level=0, word_count_target=250),
                Section(id="intro", title="Introduction", level=1, word_count_target=1500),
                Section(id="methods", title="Methods", level=1, word_count_target=1500),
                Section(id="results", title="Results", level=1, word_count_target=1500),
                Section(id="conclusion", title="Conclusion", level=1, word_count_target=500)
            ]
        )

    def test_outline_creation(self, sample_outline):
        """Test outline creation."""
        assert sample_outline.topic == "Machine Learning Research"
        assert len(sample_outline.sections) == 5
        assert sample_outline.version == "1.0"

    def test_outline_to_json_file(self, sample_outline):
        """Test saving outline to JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "outline.json"
            sample_outline.to_json_file(path)

            assert path.exists()

            with open(path) as f:
                data = json.load(f)

            assert data["topic"] == "Machine Learning Research"
            assert len(data["sections"]) == 5

    def test_outline_from_json_file(self, sample_outline):
        """Test loading outline from JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "outline.json"
            sample_outline.to_json_file(path)

            loaded = Outline.from_json_file(path)

            assert loaded.topic == sample_outline.topic
            assert len(loaded.sections) == len(sample_outline.sections)
            assert loaded.sections[0].id == "abstract"

    def test_outline_to_markdown(self, sample_outline):
        """Test outline markdown conversion."""
        markdown = sample_outline.to_markdown()

        assert "# Paper Outline: Machine Learning Research" in markdown
        assert "**Total Sections:** 5" in markdown
        assert "# Abstract" in markdown
        assert "# Introduction" in markdown

    def test_outline_get_section_by_id(self, sample_outline):
        """Test getting section by ID."""
        section = sample_outline.get_section_by_id("intro")

        assert section is not None
        assert section.title == "Introduction"

    def test_outline_get_section_by_id_not_found(self, sample_outline):
        """Test getting nonexistent section."""
        section = sample_outline.get_section_by_id("nonexistent")
        assert section is None

    def test_outline_get_section_by_id_subsection(self):
        """Test getting subsection by ID."""
        subsection = Section(id="bg", title="Background")
        intro = Section(id="intro", title="Introduction", subsections=[subsection])
        outline = Outline(topic="Test", sections=[intro])

        found = outline.get_section_by_id("bg")
        assert found is not None
        assert found.title == "Background"

    def test_outline_get_all_sections_flat(self, sample_outline):
        """Test flattening all sections."""
        flat = sample_outline.get_all_sections_flat()

        assert len(flat) == 5
        assert flat[0].id == "abstract"

    def test_outline_get_all_sections_flat_with_subsections(self):
        """Test flattening with nested subsections."""
        subsection = Section(id="bg", title="Background")
        intro = Section(id="intro", title="Introduction", subsections=[subsection])
        outline = Outline(topic="Test", sections=[intro])

        flat = outline.get_all_sections_flat()

        assert len(flat) == 2
        assert flat[1].id == "bg"

    def test_outline_validate_structure_valid(self, sample_outline):
        """Test structure validation passes for valid outline."""
        assert sample_outline.validate_structure() is True

    def test_outline_validate_structure_duplicate_ids(self):
        """Test structure validation fails with duplicate IDs."""
        outline = Outline(
            topic="Test",
            sections=[
                Section(id="intro", title="Introduction"),
                Section(id="intro", title="Another Intro")  # Duplicate
            ]
        )

        assert outline.validate_structure() is False

    def test_outline_validate_structure_empty_title(self):
        """Test structure validation fails with empty title."""
        outline = Outline(
            topic="Test",
            sections=[
                Section(id="intro", title="")  # Empty title
            ]
        )

        assert outline.validate_structure() is False


class TestOutlineGenerator:
    """Tests for OutlineGenerator."""

    @pytest.fixture
    def mock_claude_client(self):
        """Create a mocked Claude client."""
        return Mock()

    def test_generator_initialization(self, mock_claude_client):
        """Test generator initialization."""
        generator = OutlineGenerator(mock_claude_client)
        assert generator.claude_client == mock_claude_client

    def test_generate_outline(self, mock_claude_client):
        """Test outline generation with mocked API response."""
        # Mock Claude response with JSON
        mock_response = '''
        ```json
        {
            "sections": [
                {
                    "id": "abstract",
                    "title": "Abstract",
                    "level": 0,
                    "order": 0,
                    "objectives": ["Summarize"],
                    "key_points": ["Overview"],
                    "word_count_target": 250,
                    "sources": [],
                    "subsections": []
                },
                {
                    "id": "introduction",
                    "title": "Introduction",
                    "level": 1,
                    "order": 1,
                    "objectives": ["Introduce topic"],
                    "key_points": ["Background"],
                    "word_count_target": 1500,
                    "sources": [],
                    "subsections": []
                }
            ]
        }
        ```
        '''
        mock_claude_client.generate.return_value = mock_response

        with patch('papergen.ai.prompts.PromptLibrary') as mock_prompts:
            mock_prompts.outline_generation.return_value = ("system", "user")

            generator = OutlineGenerator(mock_claude_client)
            outline = generator.generate(
                topic="AI Research",
                research_text="Research content here...",
                sections=["Abstract", "Introduction"]
            )

        assert outline.topic == "AI Research"
        assert len(outline.sections) == 2
        assert outline.sections[0].id == "abstract"

    def test_generate_outline_fallback(self, mock_claude_client):
        """Test outline generation with fallback when parsing fails."""
        # Mock invalid response
        mock_claude_client.generate.return_value = "Invalid response without JSON"

        with patch('papergen.ai.prompts.PromptLibrary') as mock_prompts:
            mock_prompts.outline_generation.return_value = ("system", "user")

            generator = OutlineGenerator(mock_claude_client)
            outline = generator.generate(
                topic="Test Topic",
                research_text="Content",
                sections=["Introduction"]
            )

        # Should create fallback outline
        assert outline.topic == "Test Topic"
        assert len(outline.sections) > 0
        assert outline.sections[0].id == "abstract"

    def test_parse_outline_response_json_block(self, mock_claude_client):
        """Test parsing JSON from code block."""
        generator = OutlineGenerator(mock_claude_client)

        response = '''
        Here's the outline:
        ```json
        {"sections": [{"id": "test", "title": "Test", "level": 1, "order": 0}]}
        ```
        '''

        result = generator._parse_outline_response(response, "topic")
        assert "sections" in result
        assert result["sections"][0]["id"] == "test"

    def test_parse_outline_response_raw_json(self, mock_claude_client):
        """Test parsing raw JSON."""
        generator = OutlineGenerator(mock_claude_client)

        response = '{"sections": [{"id": "test", "title": "Test"}]}'

        result = generator._parse_outline_response(response, "topic")
        assert result["sections"][0]["id"] == "test"

    def test_create_fallback_outline(self, mock_claude_client):
        """Test fallback outline creation."""
        generator = OutlineGenerator(mock_claude_client)

        fallback = generator._create_fallback_outline("Test Topic")

        assert "sections" in fallback
        section_ids = [s["id"] for s in fallback["sections"]]
        assert "abstract" in section_ids
        assert "introduction" in section_ids
        assert "methods" in section_ids
        assert "results" in section_ids
        assert "conclusion" in section_ids
