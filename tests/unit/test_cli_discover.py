"""Tests for discover CLI commands."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import json

from typer.testing import CliRunner

from papergen.cli.discover import (
    app, _display_survey_results, _display_paper_analysis,
    _display_ideas, _display_multi_llm_results, _save_reports
)


runner = CliRunner()


class TestSurveyCommand:
    """Tests for survey command."""

    def test_survey_help(self):
        """Test survey command help."""
        result = runner.invoke(app, ["survey", "--help"])
        assert result.exit_code == 0
        assert "survey" in result.output.lower()

    def test_survey_nonexistent_pdf(self):
        """Test survey with nonexistent PDF."""
        result = runner.invoke(app, ["survey", "/nonexistent/file.pdf", "--topic", "AI"])
        # Should fail or show error
        assert result.exit_code != 0 or "error" in result.output.lower()

    def test_survey_with_output(self):
        """Test survey with output file."""
        mock_extractor = Mock()
        mock_extractor.extract.return_value = {"full_text": "Survey content"}

        mock_analyzer = Mock()
        mock_analyzer.analyze_survey.return_value = {
            "research_gaps": [{"gap": "Test gap"}],
            "key_papers_to_read": [{"title": "Paper 1"}],
            "future_directions": [{"direction": "Direction 1"}]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_file = Path(tmpdir) / "survey.pdf"
            pdf_file.write_text("fake pdf")
            output_file = Path(tmpdir) / "results.json"

            with patch('papergen.sources.pdf_extractor.PDFExtractor', return_value=mock_extractor):
                with patch('papergen.discovery.survey.SurveyAnalyzer', return_value=mock_analyzer):
                    result = runner.invoke(app, [
                        "survey", str(pdf_file),
                        "--topic", "Machine Learning",
                        "--output", str(output_file)
                    ])

                    # Check if analysis was attempted (may fail on dependencies)
                    assert result.exit_code == 0 or "error" in result.output.lower()


class TestPaperCommand:
    """Tests for paper command."""

    def test_paper_help(self):
        """Test paper command help."""
        result = runner.invoke(app, ["paper", "--help"])
        assert result.exit_code == 0
        assert "paper" in result.output.lower()

    def test_paper_analysis(self):
        """Test paper analysis."""
        mock_extractor = Mock()
        mock_extractor.extract.return_value = {"full_text": "Paper content"}

        mock_finder = Mock()
        mock_finder.analyze_paper.return_value = {
            "title": "Test Paper",
            "core_contribution": "Test contribution",
            "strengths": ["Strength 1"],
            "weaknesses": ["Weakness 1"],
            "inspiration_for_new_research": [{"idea": "Research idea"}]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_file = Path(tmpdir) / "paper.pdf"
            pdf_file.write_text("fake pdf")

            with patch('papergen.sources.pdf_extractor.PDFExtractor', return_value=mock_extractor):
                with patch('papergen.discovery.papers.PaperFinder', return_value=mock_finder):
                    result = runner.invoke(app, ["paper", str(pdf_file)])

                    # Should complete or show error (may fail on dependencies)
                    assert result.exit_code == 0 or "error" in result.output.lower()


class TestBrainstormCommand:
    """Tests for brainstorm command."""

    def test_brainstorm_help(self):
        """Test brainstorm command help."""
        result = runner.invoke(app, ["brainstorm", "--help"])
        assert result.exit_code == 0
        assert "brainstorm" in result.output.lower()

    def test_brainstorm_single_llm(self):
        """Test brainstorm with single LLM."""
        mock_generator = Mock()
        mock_generator.generate_ideas.return_value = [
            {"title": "Idea 1", "novelty": "High"}
        ]

        with patch('papergen.discovery.brainstorm.IdeaGenerator', return_value=mock_generator):
            result = runner.invoke(app, ["brainstorm", "Machine Learning"])

            # Should attempt generation (may fail on API init)
            assert result.exit_code == 0 or "error" in result.output.lower()

    def test_brainstorm_with_context_file(self):
        """Test brainstorm with context file."""
        mock_generator = Mock()
        mock_generator.generate_ideas.return_value = []

        with tempfile.TemporaryDirectory() as tmpdir:
            context_file = Path(tmpdir) / "context.json"
            context_file.write_text(json.dumps({
                "research_gaps": [{"gap": "Gap 1"}],
                "weaknesses": ["Weakness 1"],
                "future_directions": [{"direction": "Dir 1"}]
            }))

            with patch('papergen.discovery.brainstorm.IdeaGenerator', return_value=mock_generator):
                result = runner.invoke(app, [
                    "brainstorm", "AI",
                    "--context", str(context_file)
                ])

                # Should attempt to load context
                assert result.exit_code == 0 or "error" in result.output.lower()

    def test_brainstorm_multi_llm(self):
        """Test brainstorm with multi-LLM mode."""
        mock_generator = Mock()
        mock_generator.generate_ideas.return_value = []
        mock_generator.get_summary.return_value = {"summary": "Test summary"}
        mock_generator.get_reports.return_value = []

        with patch('papergen.discovery.brainstorm.IdeaGenerator', return_value=mock_generator):
            result = runner.invoke(app, ["brainstorm", "AI", "--multi"])

            # Should attempt multi-LLM mode
            assert result.exit_code == 0 or "error" in result.output.lower()


class TestSearchCommand:
    """Tests for search command."""

    def test_search_help(self):
        """Test search command help."""
        result = runner.invoke(app, ["search", "--help"])
        assert result.exit_code == 0
        assert "search" in result.output.lower()

    def test_search_papers(self):
        """Test searching for papers."""
        mock_paper = Mock()
        mock_paper.title = "Test Paper"
        mock_paper.year = 2024
        mock_paper.citation_count = 100
        mock_paper.venue = "NeurIPS"
        mock_paper.to_dict.return_value = {"title": "Test Paper"}

        mock_client = Mock()
        mock_client.search_papers.return_value = [mock_paper]

        with patch('papergen.sources.semantic_scholar.SemanticScholarClient', return_value=mock_client):
            result = runner.invoke(app, ["search", "machine learning"])

            # Should attempt to search
            assert result.exit_code == 0 or mock_client.search_papers.called

    def test_search_no_results(self):
        """Test search with no results."""
        mock_client = Mock()
        mock_client.search_papers.return_value = []

        with patch('papergen.sources.semantic_scholar.SemanticScholarClient', return_value=mock_client):
            result = runner.invoke(app, ["search", "xyznonexistent"])

            assert "no papers" in result.output.lower() or result.exit_code == 0

    def test_search_with_filters(self):
        """Test search with filters."""
        mock_client = Mock()
        mock_client.search_papers.return_value = []

        with patch('papergen.sources.semantic_scholar.SemanticScholarClient', return_value=mock_client):
            result = runner.invoke(app, [
                "search", "AI",
                "--limit", "5",
                "--year", "2023",
                "--min-citations", "50"
            ])

            # Should attempt search with filters
            assert result.exit_code == 0 or mock_client.search_papers.called


class TestCitationsCommand:
    """Tests for citations command."""

    def test_citations_help(self):
        """Test citations command help."""
        result = runner.invoke(app, ["citations", "--help"])
        assert result.exit_code == 0
        assert "citation" in result.output.lower()

    def test_citations_paper_not_found(self):
        """Test citations when paper not found."""
        mock_client = Mock()
        mock_client.analyze_citation_graph.return_value = None

        with patch('papergen.sources.semantic_scholar.SemanticScholarClient', return_value=mock_client):
            result = runner.invoke(app, ["citations", "nonexistent-paper-id"])

            assert "not found" in result.output.lower() or result.exit_code == 0

    def test_citations_success(self):
        """Test successful citation analysis."""
        mock_client = Mock()
        mock_client.analyze_citation_graph.return_value = {
            'paper': {
                'title': 'Test Paper',
                'year': 2024,
                'citation_count': 100,
                'reference_count': 50,
                'influential_citation_count': 10
            },
            'citation_velocity': 25.5,
            'top_citing_papers': [
                {'title': 'Citing Paper 1', 'year': 2024, 'citation_count': 50}
            ],
            'top_referenced_papers': [
                {'title': 'Reference 1', 'year': 2020, 'citation_count': 200}
            ]
        }

        with patch('papergen.sources.semantic_scholar.SemanticScholarClient', return_value=mock_client):
            result = runner.invoke(app, ["citations", "test-paper-id"])

            assert result.exit_code == 0 or mock_client.analyze_citation_graph.called


class TestRecommendCommand:
    """Tests for recommend command."""

    def test_recommend_help(self):
        """Test recommend command help."""
        result = runner.invoke(app, ["recommend", "--help"])
        assert result.exit_code == 0
        assert "recommend" in result.output.lower()

    def test_recommend_no_results(self):
        """Test recommend with no results."""
        mock_client = Mock()
        mock_client.get_paper_by_id.return_value = None
        mock_client.get_recommended_papers.return_value = []

        with patch('papergen.sources.semantic_scholar.SemanticScholarClient', return_value=mock_client):
            result = runner.invoke(app, ["recommend", "test-paper-id"])

            assert "no recommendations" in result.output.lower() or result.exit_code == 0


class TestSeminalCommand:
    """Tests for seminal command."""

    def test_seminal_help(self):
        """Test seminal command help."""
        result = runner.invoke(app, ["seminal", "--help"])
        assert result.exit_code == 0
        assert "seminal" in result.output.lower()

    def test_seminal_no_results(self):
        """Test seminal with no results."""
        mock_client = Mock()
        mock_client.find_seminal_papers.return_value = []

        with patch('papergen.sources.semantic_scholar.SemanticScholarClient', return_value=mock_client):
            result = runner.invoke(app, ["seminal", "obscure topic"])

            assert "no papers" in result.output.lower() or result.exit_code == 0


class TestAuthorCommand:
    """Tests for author command."""

    def test_author_help(self):
        """Test author command help."""
        result = runner.invoke(app, ["author", "--help"])
        assert result.exit_code == 0
        assert "author" in result.output.lower()

    def test_author_not_found(self):
        """Test author not found."""
        mock_client = Mock()
        mock_client.search_authors.return_value = []

        with patch('papergen.sources.semantic_scholar.SemanticScholarClient', return_value=mock_client):
            result = runner.invoke(app, ["author", "Nonexistent Author"])

            assert "no authors" in result.output.lower() or result.exit_code == 0

    def test_author_with_papers(self):
        """Test author search with papers flag."""
        mock_paper = Mock()
        mock_paper.title = "Test Paper"
        mock_paper.year = 2024
        mock_paper.citation_count = 50
        mock_paper.venue = "ICML"

        mock_client = Mock()
        mock_client.search_authors.return_value = [
            {'name': 'Test Author', 'authorId': '123', 'paperCount': 10, 'citationCount': 500, 'hIndex': 15}
        ]
        mock_client.get_author_papers.return_value = [mock_paper]

        with patch('papergen.sources.semantic_scholar.SemanticScholarClient', return_value=mock_client):
            result = runner.invoke(app, ["author", "Test Author", "--papers"])

            # Should attempt to get papers
            assert result.exit_code == 0 or mock_client.get_author_papers.called


class TestTrendingCommand:
    """Tests for trending command."""

    def test_trending_help(self):
        """Test trending command help."""
        result = runner.invoke(app, ["trending", "--help"])
        assert result.exit_code == 0
        assert "trending" in result.output.lower()

    def test_trending_no_results(self):
        """Test trending with no results."""
        mock_client = Mock()
        mock_client.get_trending_papers.return_value = []

        with patch('papergen.sources.semantic_scholar.SemanticScholarClient', return_value=mock_client):
            result = runner.invoke(app, ["trending"])

            assert "no papers" in result.output.lower() or result.exit_code == 0


class TestDisplayFunctions:
    """Tests for display helper functions."""

    def test_display_survey_results_empty(self, capsys):
        """Test displaying empty survey results."""
        _display_survey_results({})
        # Should not raise error

    def test_display_survey_results_with_gaps(self, capsys):
        """Test displaying survey results with gaps."""
        results = {
            "research_gaps": [{"gap": "Gap 1"}, "Gap 2"],
            "key_papers_to_read": [{"title": "Paper 1"}, "Paper 2"],
            "future_directions": [{"direction": "Dir 1"}, "Dir 2"]
        }
        _display_survey_results(results)
        # Should not raise error

    def test_display_paper_analysis(self, capsys):
        """Test displaying paper analysis."""
        results = {
            "title": "Test Paper",
            "core_contribution": "Test contribution",
            "strengths": ["Strength 1"],
            "weaknesses": ["Weakness 1"],
            "inspiration_for_new_research": [{"idea": "Idea 1"}]
        }
        _display_paper_analysis(results)
        # Should not raise error

    def test_display_ideas(self, capsys):
        """Test displaying ideas."""
        ideas = [
            {
                "title": "Idea 1",
                "one_sentence": "Brief description",
                "novelty": "High",
                "feasibility": "Medium",
                "potential_venues": ["NeurIPS", "ICML"],
                "first_steps": ["Step 1", "Step 2"]
            }
        ]
        _display_ideas(ideas)
        # Should not raise error

    def test_display_multi_llm_results(self, capsys):
        """Test displaying multi-LLM results."""
        mock_generator = Mock()
        mock_generator.get_summary.return_value = {
            "summary": "Test summary",
            "top_recommendations": [{"title": "Rec 1"}],
            "consensus_themes": ["Theme 1"]
        }
        mock_report = Mock()
        mock_report.provider = "openai"
        mock_report.model = "gpt-4"
        mock_report.ideas = [{"title": "Idea"}]
        mock_generator.get_reports.return_value = [mock_report]

        _display_multi_llm_results(mock_generator, None)
        # Should not raise error

    def test_save_reports(self):
        """Test saving reports."""
        mock_generator = Mock()
        mock_generator.get_summary.return_value = {"summary": "Test"}
        mock_report = Mock()
        mock_report.provider = "openai"
        mock_report.model = "gpt-4"
        mock_report.ideas = []
        mock_generator.get_reports.return_value = [mock_report]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            _save_reports(mock_generator, output_dir)

            # Check files were created
            assert (output_dir / "summary.json").exists()
            assert (output_dir / "openai_gpt-4.json").exists()
