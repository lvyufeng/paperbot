"""Tests for research organization."""

import pytest
from unittest.mock import Mock, patch

from papergen.sources.organizer import ResearchOrganizer


class TestResearchOrganizerInit:
    """Tests for ResearchOrganizer initialization."""

    def test_init_without_client(self):
        """Test initialization without Claude client."""
        organizer = ResearchOrganizer()
        assert organizer.claude_client is None

    def test_init_with_client(self):
        """Test initialization with Claude client."""
        mock_client = Mock()
        organizer = ResearchOrganizer(claude_client=mock_client)
        assert organizer.claude_client == mock_client


class TestResearchOrganizerBasicOrganization:
    """Tests for basic organization without AI."""

    @pytest.fixture
    def organizer(self):
        """Create organizer without Claude client."""
        return ResearchOrganizer()

    @pytest.fixture
    def sample_sources(self):
        """Create sample research sources."""
        return [
            {
                "metadata": {
                    "title": "Deep Learning Paper",
                    "authors": ["John Smith", "Jane Doe"],
                    "year": 2023
                },
                "content": {
                    "abstract": "This paper presents novel deep learning techniques.",
                    "keywords": ["deep learning", "neural networks"],
                    "full_text": "Full text content of the paper..."
                }
            },
            {
                "metadata": {
                    "title": "Machine Learning Survey",
                    "authors": ["Bob Brown"]
                },
                "content": {
                    "abstract": "A comprehensive survey of ML techniques.",
                    "full_text": "Survey content here..."
                }
            }
        ]

    def test_basic_organization(self, organizer, sample_sources):
        """Test basic organization produces markdown."""
        result = organizer._basic_organization(sample_sources, "")

        assert "# Organized Research" in result
        assert "Deep Learning Paper" in result
        assert "Machine Learning Survey" in result
        assert "John Smith" in result

    def test_basic_organization_with_focus(self, organizer, sample_sources):
        """Test basic organization with focus area."""
        result = organizer._basic_organization(sample_sources, "neural networks")

        assert "**Focus:** neural networks" in result

    def test_basic_organization_includes_abstract(self, organizer, sample_sources):
        """Test that abstract is included."""
        result = organizer._basic_organization(sample_sources, "")

        assert "novel deep learning techniques" in result

    def test_basic_organization_includes_keywords(self, organizer, sample_sources):
        """Test that keywords are included."""
        result = organizer._basic_organization(sample_sources, "")

        assert "deep learning" in result
        assert "neural networks" in result

    def test_basic_organization_truncates_content(self, organizer):
        """Test that long content is truncated."""
        sources = [{
            "metadata": {"title": "Long Paper"},
            "content": {
                "full_text": "x" * 1000  # Long content
            }
        }]

        result = organizer._basic_organization(sources, "")

        assert "..." in result  # Should be truncated

    def test_basic_organization_handles_string_authors(self, organizer):
        """Test handling of authors as string instead of list."""
        sources = [{
            "metadata": {
                "title": "Paper",
                "authors": "Single Author"  # String instead of list
            },
            "content": {}
        }]

        result = organizer._basic_organization(sources, "")

        assert "Single Author" in result


class TestResearchOrganizerWithAI:
    """Tests for AI-powered organization."""

    @pytest.fixture
    def mock_client(self):
        """Create mocked Claude client."""
        client = Mock()
        client.generate.return_value = "# AI Organized Research\n\nOrganized content here..."
        return client

    @pytest.fixture
    def sample_sources(self):
        """Create sample sources."""
        return [{
            "metadata": {"title": "Test Paper", "authors": ["Author"]},
            "content": {"abstract": "Abstract", "full_text": "Content"}
        }]

    def test_organize_uses_ai(self, mock_client, sample_sources):
        """Test that organize uses Claude when available."""
        organizer = ResearchOrganizer(claude_client=mock_client)

        with patch('papergen.ai.prompts.PromptLibrary') as mock_prompts:
            mock_prompts.research_organization.return_value = ("system", "user")

            result = organizer.organize(sample_sources, topic="Test Topic")

        mock_client.generate.assert_called_once()
        assert "AI Organized Research" in result

    def test_organize_fallback_on_error(self, mock_client, sample_sources):
        """Test fallback to basic organization on AI error."""
        mock_client.generate.side_effect = Exception("API Error")

        organizer = ResearchOrganizer(claude_client=mock_client)

        with patch('papergen.ai.prompts.PromptLibrary') as mock_prompts:
            mock_prompts.research_organization.return_value = ("system", "user")

            result = organizer.organize(sample_sources)

        assert "# Organized Research" in result  # Basic organization
        assert "AI organization failed" in result

    def test_organize_without_client_uses_basic(self, sample_sources):
        """Test that organize uses basic when no client."""
        organizer = ResearchOrganizer()

        result = organizer.organize(sample_sources)

        assert "# Organized Research" in result

    def test_organize_prepares_source_texts(self, mock_client, sample_sources):
        """Test that source texts are prepared correctly."""
        organizer = ResearchOrganizer(claude_client=mock_client)

        with patch('papergen.ai.prompts.PromptLibrary') as mock_prompts:
            mock_prompts.research_organization.return_value = ("system", "user")

            organizer.organize(sample_sources, focus="ML", topic="Research")

            # Check that PromptLibrary was called with source texts
            mock_prompts.research_organization.assert_called_once()
            args = mock_prompts.research_organization.call_args
            assert args[0][1] == "ML"  # focus
            assert args[0][2] == "Research"  # topic


class TestResearchOrganizerPlaceholders:
    """Tests for placeholder methods (Phase 3 features)."""

    @pytest.fixture
    def organizer(self):
        """Create organizer."""
        return ResearchOrganizer()

    def test_identify_themes(self, organizer):
        """Test identify_themes placeholder."""
        result = organizer.identify_themes([])

        assert len(result) == 1
        assert "Phase 3" in result[0]

    def test_extract_methodologies(self, organizer):
        """Test extract_methodologies placeholder."""
        result = organizer.extract_methodologies([])

        assert len(result) == 1
        assert "Phase 3" in result[0]

    def test_find_gaps(self, organizer):
        """Test find_gaps placeholder."""
        result = organizer.find_gaps([])

        assert len(result) == 1
        assert "Phase 3" in result[0]


class TestResearchOrganizerEdgeCases:
    """Tests for edge cases."""

    @pytest.fixture
    def organizer(self):
        """Create organizer."""
        return ResearchOrganizer()

    def test_organize_empty_sources(self, organizer):
        """Test organizing empty source list."""
        result = organizer.organize([])

        assert "# Organized Research" in result
        assert "0 total" in result

    def test_organize_source_missing_metadata(self, organizer):
        """Test organizing source with missing metadata."""
        sources = [{"content": {"full_text": "Some content"}}]

        result = organizer.organize(sources)

        assert "Untitled" in result  # Default title

    def test_organize_source_missing_content(self, organizer):
        """Test organizing source with missing content."""
        sources = [{"metadata": {"title": "Paper"}}]

        result = organizer.organize(sources)

        assert "Paper" in result

    def test_basic_organization_handles_none_values(self, organizer):
        """Test handling of None values in sources."""
        sources = [{
            "metadata": {
                "title": None,
                "authors": None
            },
            "content": {
                "abstract": None,
                "keywords": None,
                "full_text": None
            }
        }]

        # Should not raise - None title becomes "None" string in output
        result = organizer._basic_organization(sources, "")
        assert "# Organized Research" in result
