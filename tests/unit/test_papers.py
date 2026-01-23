"""Tests for paper finder module."""

import pytest
from unittest.mock import Mock, patch
import json

from papergen.discovery.papers import PaperFinder


class TestPaperFinderInit:
    """Tests for PaperFinder initialization."""

    def test_init(self):
        """Test initialization."""
        with patch('papergen.discovery.papers.ClaudeClient') as mock_client:
            finder = PaperFinder()

            assert finder.papers == []
            assert finder.deep_analyses == {}
            mock_client.assert_called_once()


class TestPaperFinderAnalysis:
    """Tests for paper analysis."""

    @pytest.fixture
    def finder(self):
        """Create paper finder."""
        with patch('papergen.discovery.papers.ClaudeClient') as mock_client_class:
            mock_client = Mock()
            mock_client.generate.return_value = '''
            {
                "title": "Test Paper",
                "core_contribution": "Novel method",
                "problem_addressed": "Classification",
                "methodology": {"approach": "Deep learning"},
                "experiments": {"datasets": ["MNIST"]},
                "strengths": ["Fast"],
                "weaknesses": ["Limited data"],
                "limitations_acknowledged": [],
                "future_work_suggested": ["Scale up"],
                "inspiration_for_new_research": [{"idea": "New idea"}],
                "key_equations_or_algorithms": [],
                "reproducibility_score": "high",
                "recommended_follow_up_papers": []
            }
            '''
            mock_client_class.return_value = mock_client

            return PaperFinder()

    def test_analyze_paper(self, finder):
        """Test analyzing a paper."""
        content = "This paper presents a novel method..."
        title = "Novel Classification Method"

        analysis = finder.analyze_paper(content, title)

        assert "title" in analysis
        finder.client.generate.assert_called_once()

    def test_analysis_stored(self, finder):
        """Test that analysis is stored."""
        finder.analyze_paper("Content", "Test Paper")

        assert "Test Paper" in finder.deep_analyses

    def test_get_inspirations_after_analysis(self, finder):
        """Test getting inspirations after analysis."""
        finder.analyze_paper("Content", "Test Paper")

        inspirations = finder.get_inspirations("Test Paper")

        assert isinstance(inspirations, list)

    def test_get_inspirations_no_analysis(self, finder):
        """Test getting inspirations without analysis."""
        inspirations = finder.get_inspirations("Unknown Paper")

        assert inspirations == []

    def test_get_weaknesses_after_analysis(self, finder):
        """Test getting weaknesses after analysis."""
        finder.analyze_paper("Content", "Test Paper")

        weaknesses = finder.get_weaknesses("Test Paper")

        assert isinstance(weaknesses, list)

    def test_get_weaknesses_no_analysis(self, finder):
        """Test getting weaknesses without analysis."""
        weaknesses = finder.get_weaknesses("Unknown Paper")

        assert weaknesses == []


class TestPaperFinderPrompts:
    """Tests for prompt generation."""

    @pytest.fixture
    def finder(self):
        """Create paper finder."""
        with patch('papergen.discovery.papers.ClaudeClient'):
            return PaperFinder()

    def test_get_deep_analysis_system(self, finder):
        """Test system prompt generation."""
        system = finder._get_deep_analysis_system()

        assert "expert" in system.lower()
        assert "research" in system.lower()
        assert "analyze" in system.lower()

    def test_build_deep_analysis_prompt(self, finder):
        """Test analysis prompt generation."""
        prompt = finder._build_deep_analysis_prompt(
            content="Paper content here",
            title="Test Paper"
        )

        assert "Test Paper" in prompt
        assert "JSON" in prompt
        assert "core_contribution" in prompt


class TestPaperFinderParsing:
    """Tests for response parsing."""

    @pytest.fixture
    def finder(self):
        """Create paper finder."""
        with patch('papergen.discovery.papers.ClaudeClient'):
            return PaperFinder()

    def test_parse_valid_json(self, finder):
        """Test parsing valid JSON."""
        response = '{"title": "Test", "core_contribution": "Novel"}'

        result = finder._parse_response(response)

        assert result["title"] == "Test"

    def test_parse_json_with_text(self, finder):
        """Test parsing JSON embedded in text."""
        response = '''
        Here is my analysis:
        {"title": "Test", "core_contribution": "Novel"}
        That's my analysis.
        '''

        result = finder._parse_response(response)

        assert result["title"] == "Test"

    def test_parse_invalid_json(self, finder):
        """Test parsing invalid JSON."""
        response = "This is not JSON at all"

        result = finder._parse_response(response)

        assert "raw_response" in result
        assert result["raw_response"] == response


class TestPaperFinderLongContent:
    """Tests for handling long content."""

    def test_truncates_long_content(self):
        """Test that long content is truncated."""
        with patch('papergen.discovery.papers.ClaudeClient') as mock_client_class:
            mock_client = Mock()
            mock_client.generate.return_value = '{"title": "Test"}'
            mock_client_class.return_value = mock_client

            finder = PaperFinder()

            # Create very long content
            long_content = "x" * 100000
            finder.analyze_paper(long_content, "Long Paper")

            # Check that the prompt was built with truncated content
            call_args = mock_client.generate.call_args
            prompt = call_args.kwargs.get('prompt', call_args[0][0] if call_args[0] else '')
            # The prompt builder truncates to 40000 chars
            assert len(prompt) < 100000


class TestPaperFinderEdgeCases:
    """Tests for edge cases."""

    @pytest.fixture
    def finder(self):
        """Create paper finder."""
        with patch('papergen.discovery.papers.ClaudeClient') as mock_client_class:
            mock_client = Mock()
            mock_client.generate.return_value = '{}'
            mock_client_class.return_value = mock_client

            return PaperFinder()

    def test_analyze_empty_content(self, finder):
        """Test analyzing empty content."""
        analysis = finder.analyze_paper("", "Empty Paper")

        # Should still return something
        assert isinstance(analysis, dict)

    def test_analyze_special_characters_title(self, finder):
        """Test analyzing paper with special characters in title."""
        analysis = finder.analyze_paper(
            "Content",
            "Test: A Novel Approach - Part 1 (Extended)"
        )

        assert isinstance(analysis, dict)

    def test_multiple_analyses(self, finder):
        """Test analyzing multiple papers."""
        finder.analyze_paper("Content 1", "Paper 1")
        finder.analyze_paper("Content 2", "Paper 2")

        assert "Paper 1" in finder.deep_analyses
        assert "Paper 2" in finder.deep_analyses
        assert len(finder.deep_analyses) == 2
