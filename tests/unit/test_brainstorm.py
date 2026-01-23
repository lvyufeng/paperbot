"""Tests for brainstorm module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json

from papergen.discovery.brainstorm import IdeaGenerator, BrainstormReport


class TestBrainstormReport:
    """Tests for BrainstormReport dataclass."""

    def test_create_report(self):
        """Test creating a brainstorm report."""
        report = BrainstormReport(
            provider="anthropic",
            model="claude-3",
            ideas=[{"title": "Test Idea"}],
            raw_response="Raw response text"
        )

        assert report.provider == "anthropic"
        assert report.model == "claude-3"
        assert len(report.ideas) == 1
        assert report.raw_response == "Raw response text"


class TestIdeaGeneratorInit:
    """Tests for IdeaGenerator initialization."""

    def test_init_single_llm(self):
        """Test initialization with single LLM."""
        with patch('papergen.discovery.brainstorm.ClaudeClient') as mock_client:
            generator = IdeaGenerator(use_multi_llm=False)

            assert generator.use_multi_llm is False
            assert generator.multi_llm is None
            assert generator.ideas == []
            assert generator.context == {}

    def test_init_multi_llm(self):
        """Test initialization with multi LLM."""
        with patch('papergen.discovery.brainstorm.ClaudeClient'):
            with patch('papergen.discovery.brainstorm.MultiLLMManager') as mock_multi:
                mock_multi.from_env.return_value = Mock()

                generator = IdeaGenerator(use_multi_llm=True)

                assert generator.use_multi_llm is True
                assert generator.multi_llm is not None


class TestIdeaGeneratorContext:
    """Tests for setting context."""

    @pytest.fixture
    def generator(self):
        """Create generator."""
        with patch('papergen.discovery.brainstorm.ClaudeClient'):
            return IdeaGenerator(use_multi_llm=False)

    def test_set_context(self, generator):
        """Test setting research context."""
        generator.set_context(
            topic="Machine Learning",
            research_gaps=[{"gap": "No efficient training"}],
            paper_weaknesses=["Scalability issues"],
            future_directions=[{"direction": "Distributed learning"}]
        )

        assert generator.context["topic"] == "Machine Learning"
        assert len(generator.context["gaps"]) == 1
        assert len(generator.context["weaknesses"]) == 1
        assert len(generator.context["directions"]) == 1


class TestIdeaGeneratorPrompts:
    """Tests for prompt generation."""

    @pytest.fixture
    def generator(self):
        """Create generator with context."""
        with patch('papergen.discovery.brainstorm.ClaudeClient'):
            gen = IdeaGenerator(use_multi_llm=False)
            gen.set_context(
                topic="NLP Research",
                research_gaps=[{"gap": "Low-resource languages"}],
                paper_weaknesses=["Data requirements"],
                future_directions=[{"direction": "Zero-shot learning"}]
            )
            return gen

    def test_get_brainstorm_system(self, generator):
        """Test system prompt generation."""
        system = generator._get_brainstorm_system()

        assert "research advisor" in system.lower()
        assert "novel" in system.lower()

    def test_build_brainstorm_prompt(self, generator):
        """Test user prompt generation."""
        prompt = generator._build_brainstorm_prompt(num_ideas=5)

        assert "NLP Research" in prompt
        assert "Low-resource languages" in prompt
        assert "5" in prompt
        assert "JSON" in prompt


class TestIdeaGeneratorParsing:
    """Tests for response parsing."""

    @pytest.fixture
    def generator(self):
        """Create generator."""
        with patch('papergen.discovery.brainstorm.ClaudeClient'):
            return IdeaGenerator(use_multi_llm=False)

    def test_parse_valid_json(self, generator):
        """Test parsing valid JSON response."""
        response = '''Some text before
        {"ideas": [{"title": "Test Idea", "novelty": "High"}]}
        Some text after'''

        ideas = generator._parse_ideas(response)

        assert len(ideas) == 1
        assert ideas[0]["title"] == "Test Idea"

    def test_parse_invalid_json(self, generator):
        """Test parsing invalid JSON response."""
        response = "This is not JSON at all"

        ideas = generator._parse_ideas(response)

        # When no JSON is found, returns empty list
        assert ideas == []

    def test_parse_json_without_ideas_key(self, generator):
        """Test parsing JSON without ideas key."""
        response = '{"title": "Single Idea", "novelty": "High"}'

        ideas = generator._parse_ideas(response)

        # Should wrap single object
        assert len(ideas) == 1


class TestIdeaGeneratorGeneration:
    """Tests for idea generation."""

    @pytest.fixture
    def generator(self):
        """Create generator with context."""
        with patch('papergen.discovery.brainstorm.ClaudeClient') as mock_client_class:
            mock_client = Mock()
            mock_client.generate.return_value = '{"ideas": [{"title": "Test Idea"}]}'
            mock_client_class.return_value = mock_client

            gen = IdeaGenerator(use_multi_llm=False)
            gen.set_context(
                topic="AI",
                research_gaps=[],
                paper_weaknesses=[],
                future_directions=[]
            )
            return gen

    def test_generate_single_llm(self, generator):
        """Test idea generation with single LLM."""
        ideas = generator.generate_ideas(num_ideas=3)

        assert len(ideas) >= 1
        generator.client.generate.assert_called_once()

    def test_generate_stores_ideas(self, generator):
        """Test that generated ideas are stored."""
        generator.generate_ideas(num_ideas=3)

        assert len(generator.ideas) >= 1


class TestIdeaGeneratorMultiLLM:
    """Tests for multi-LLM generation."""

    def test_generate_multi_llm(self):
        """Test generation with multiple LLMs."""
        with patch('papergen.discovery.brainstorm.ClaudeClient') as mock_client_class:
            mock_client = Mock()
            mock_client.generate.return_value = '{"unique_ideas": [{"title": "Idea"}]}'
            mock_client_class.return_value = mock_client

            with patch('papergen.discovery.brainstorm.MultiLLMManager') as mock_multi_class:
                mock_multi = Mock()
                mock_response = Mock()
                mock_response.success = True
                mock_response.content = '{"ideas": [{"title": "LLM1 Idea"}]}'
                mock_response.provider = "openai"
                mock_response.model = "gpt-4"
                mock_multi.generate_parallel.return_value = [mock_response]
                mock_multi_class.from_env.return_value = mock_multi

                generator = IdeaGenerator(use_multi_llm=True)
                generator.set_context(
                    topic="AI",
                    research_gaps=[],
                    paper_weaknesses=[],
                    future_directions=[]
                )

                ideas = generator.generate_ideas(num_ideas=3)

                mock_multi.generate_parallel.assert_called_once()
                assert len(generator.reports) == 1


class TestIdeaGeneratorEvaluation:
    """Tests for idea evaluation."""

    @pytest.fixture
    def generator(self):
        """Create generator with ideas."""
        with patch('papergen.discovery.brainstorm.ClaudeClient') as mock_client_class:
            mock_client = Mock()
            mock_client.generate.return_value = "Evaluation: Good idea"
            mock_client_class.return_value = mock_client

            gen = IdeaGenerator(use_multi_llm=False)
            gen.ideas = [
                {"title": "Test Idea", "problem": "Problem X", "method_sketch": "Method Y"}
            ]
            return gen

    def test_evaluate_valid_idea(self, generator):
        """Test evaluating a valid idea."""
        result = generator.evaluate_idea(0)

        assert "idea" in result
        assert "evaluation" in result
        generator.client.generate.assert_called_once()

    def test_evaluate_invalid_index(self, generator):
        """Test evaluating with invalid index."""
        result = generator.evaluate_idea(99)

        assert "error" in result


class TestIdeaGeneratorSummary:
    """Tests for idea summarization."""

    @pytest.fixture
    def generator(self):
        """Create generator."""
        with patch('papergen.discovery.brainstorm.ClaudeClient') as mock_client_class:
            mock_client = Mock()
            mock_client.generate.return_value = '{"unique_ideas": [], "summary": "Test summary"}'
            mock_client_class.return_value = mock_client

            return IdeaGenerator(use_multi_llm=False)

    def test_summarize_empty_ideas(self, generator):
        """Test summarizing empty idea list."""
        summary = generator._summarize_ideas([])

        assert summary["unique_ideas"] == []
        assert "No ideas" in summary["summary"]

    def test_summarize_ideas(self, generator):
        """Test summarizing ideas list."""
        ideas = [
            {"title": "Idea 1"},
            {"title": "Idea 2"}
        ]

        summary = generator._summarize_ideas(ideas)

        generator.client.generate.assert_called_once()

    def test_get_reports(self, generator):
        """Test getting reports."""
        generator.reports = [BrainstormReport("a", "b", [], "")]
        reports = generator.get_reports()

        assert len(reports) == 1

    def test_get_summary(self, generator):
        """Test getting summary."""
        generator.summary = {"test": "summary"}
        summary = generator.get_summary()

        assert summary["test"] == "summary"
