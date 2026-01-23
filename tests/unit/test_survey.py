"""Tests for SurveyAnalyzer."""

import pytest
from unittest.mock import Mock, patch
import json


class TestSurveyAnalyzerInit:
    """Tests for SurveyAnalyzer initialization."""

    def test_init(self):
        """Test initialization."""
        mock_client = Mock()

        with patch('papergen.discovery.survey.ClaudeClient', return_value=mock_client):
            from papergen.discovery.survey import SurveyAnalyzer
            analyzer = SurveyAnalyzer()

            assert analyzer.client == mock_client
            assert analyzer.analysis_results == {}


class TestSurveyAnalyzerAnalyze:
    """Tests for analyze_survey method."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        mock_client = Mock()
        mock_client.generate.return_value = json.dumps({
            "topic": "Machine Learning",
            "research_gaps": [{"gap": "Gap 1"}],
            "key_papers_to_read": [{"title": "Paper 1"}],
            "future_directions": [{"direction": "Direction 1"}]
        })

        with patch('papergen.discovery.survey.ClaudeClient', return_value=mock_client):
            from papergen.discovery.survey import SurveyAnalyzer
            return SurveyAnalyzer()

    def test_analyze_survey(self, analyzer):
        """Test analyzing survey."""
        content = "Survey content about machine learning..."
        topic = "Machine Learning"

        result = analyzer.analyze_survey(content, topic)

        assert "research_gaps" in result
        assert analyzer.client.generate.called

    def test_analyze_survey_stores_results(self, analyzer):
        """Test that results are stored."""
        content = "Survey content"
        topic = "AI"

        result = analyzer.analyze_survey(content, topic)

        assert analyzer.analysis_results == result


class TestSurveyAnalyzerPrompts:
    """Tests for prompt methods."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        mock_client = Mock()

        with patch('papergen.discovery.survey.ClaudeClient', return_value=mock_client):
            from papergen.discovery.survey import SurveyAnalyzer
            return SurveyAnalyzer()

    def test_get_system_prompt(self, analyzer):
        """Test system prompt generation."""
        system = analyzer._get_system_prompt()

        assert "research" in system.lower()
        assert "expert" in system.lower()
        assert "JSON" in system

    def test_build_analysis_prompt(self, analyzer):
        """Test analysis prompt building."""
        content = "Test survey content"
        topic = "Neural Networks"

        prompt = analyzer._build_analysis_prompt(content, topic)

        assert topic in prompt
        assert "research_gaps" in prompt
        assert "future_directions" in prompt


class TestSurveyAnalyzerParsing:
    """Tests for response parsing."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        mock_client = Mock()

        with patch('papergen.discovery.survey.ClaudeClient', return_value=mock_client):
            from papergen.discovery.survey import SurveyAnalyzer
            return SurveyAnalyzer()

    def test_parse_valid_json(self, analyzer):
        """Test parsing valid JSON response."""
        response = json.dumps({
            "research_gaps": [{"gap": "Test gap"}],
            "key_papers_to_read": [{"title": "Paper"}]
        })

        result = analyzer._parse_analysis(response)

        assert "research_gaps" in result
        assert result["research_gaps"][0]["gap"] == "Test gap"

    def test_parse_json_with_surrounding_text(self, analyzer):
        """Test parsing JSON with surrounding text."""
        response = '''Here is the analysis:
        {"research_gaps": [{"gap": "Gap 1"}]}
        Let me know if you need more.'''

        result = analyzer._parse_analysis(response)

        assert "research_gaps" in result

    def test_parse_invalid_json(self, analyzer):
        """Test parsing invalid JSON returns raw response."""
        response = "This is not valid JSON at all"

        result = analyzer._parse_analysis(response)

        assert "raw_response" in result
        assert result["raw_response"] == response


class TestSurveyAnalyzerGetters:
    """Tests for getter methods."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer with results."""
        mock_client = Mock()

        with patch('papergen.discovery.survey.ClaudeClient', return_value=mock_client):
            from papergen.discovery.survey import SurveyAnalyzer
            analyzer = SurveyAnalyzer()
            analyzer.analysis_results = {
                "research_gaps": [{"gap": "Gap 1"}, {"gap": "Gap 2"}],
                "key_papers_to_read": [{"title": "Paper 1"}],
                "future_directions": [{"direction": "Direction 1"}]
            }
            return analyzer

    def test_get_research_gaps(self, analyzer):
        """Test getting research gaps."""
        gaps = analyzer.get_research_gaps()

        assert len(gaps) == 2
        assert gaps[0]["gap"] == "Gap 1"

    def test_get_key_papers(self, analyzer):
        """Test getting key papers."""
        papers = analyzer.get_key_papers()

        assert len(papers) == 1
        assert papers[0]["title"] == "Paper 1"

    def test_get_future_directions(self, analyzer):
        """Test getting future directions."""
        directions = analyzer.get_future_directions()

        assert len(directions) == 1
        assert directions[0]["direction"] == "Direction 1"

    def test_getters_empty_results(self):
        """Test getters with empty results."""
        mock_client = Mock()

        with patch('papergen.discovery.survey.ClaudeClient', return_value=mock_client):
            from papergen.discovery.survey import SurveyAnalyzer
            analyzer = SurveyAnalyzer()

            assert analyzer.get_research_gaps() == []
            assert analyzer.get_key_papers() == []
            assert analyzer.get_future_directions() == []
