"""Tests for Semantic Scholar API client."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
from datetime import datetime

from papergen.sources.semantic_scholar import (
    Paper,
    RateLimiter,
    SemanticScholarClient
)


class TestPaper:
    """Tests for Paper dataclass."""

    def test_paper_creation(self):
        """Test creating a Paper instance."""
        paper = Paper(
            paper_id="abc123",
            title="Test Paper",
            year=2023,
            authors=[{"name": "John Smith"}],
            abstract="This is a test abstract",
            citation_count=100,
            reference_count=50,
            influential_citation_count=10,
            venue="ICML",
            url="https://example.com/paper",
            arxiv_id="2301.12345",
            doi="10.1234/test",
            fields_of_study=["Computer Science"]
        )

        assert paper.paper_id == "abc123"
        assert paper.title == "Test Paper"
        assert paper.year == 2023
        assert paper.citation_count == 100

    def test_paper_from_api_response(self):
        """Test creating Paper from API response."""
        api_data = {
            "paperId": "xyz789",
            "title": "API Paper",
            "year": 2022,
            "authors": [{"name": "Jane Doe", "authorId": "123"}],
            "abstract": "An abstract",
            "citationCount": 50,
            "referenceCount": 25,
            "influentialCitationCount": 5,
            "venue": "NeurIPS",
            "url": "https://example.com",
            "externalIds": {"ArXiv": "2201.00001", "DOI": "10.5678/paper"},
            "fieldsOfStudy": ["AI", "ML"]
        }

        paper = Paper.from_api_response(api_data)

        assert paper.paper_id == "xyz789"
        assert paper.title == "API Paper"
        assert paper.year == 2022
        assert paper.arxiv_id == "2201.00001"
        assert paper.doi == "10.5678/paper"
        assert "AI" in paper.fields_of_study

    def test_paper_from_api_response_missing_fields(self):
        """Test creating Paper with missing optional fields."""
        api_data = {
            "paperId": "minimal",
            "title": "Minimal Paper"
        }

        paper = Paper.from_api_response(api_data)

        assert paper.paper_id == "minimal"
        assert paper.year is None
        assert paper.abstract is None
        assert paper.citation_count == 0
        assert paper.arxiv_id is None

    def test_paper_to_dict(self):
        """Test converting Paper to dictionary."""
        paper = Paper(
            paper_id="test",
            title="Test",
            year=2024,
            authors=[{"name": "Author One"}, {"name": "Author Two"}],
            abstract="Abstract",
            citation_count=10,
            reference_count=5,
            influential_citation_count=2,
            venue="Conference",
            url="https://url.com",
            arxiv_id="2401.00001",
            doi="10.1234/test",
            fields_of_study=["CS"]
        )

        data = paper.to_dict()

        assert data["paper_id"] == "test"
        assert data["authors"] == ["Author One", "Author Two"]
        assert data["citation_count"] == 10


class TestRateLimiter:
    """Tests for RateLimiter."""

    def test_rate_limiter_creation(self):
        """Test creating rate limiter."""
        limiter = RateLimiter(requests_per_second=5.0)
        assert limiter.min_interval == 0.2

    def test_rate_limiter_default(self):
        """Test default rate limit."""
        limiter = RateLimiter()
        assert limiter.min_interval == 0.1  # 10 requests per second

    @patch('papergen.sources.semantic_scholar.time.sleep')
    @patch('papergen.sources.semantic_scholar.time.time')
    def test_rate_limiter_waits(self, mock_time, mock_sleep):
        """Test that rate limiter waits when needed."""
        # Simulate time progression
        mock_time.side_effect = [0.0, 0.05, 0.15]  # First call, check, after wait

        limiter = RateLimiter(requests_per_second=10.0)  # 0.1 second interval
        limiter.last_request_time = 0.0

        limiter.wait_if_needed()

        # Should have slept for ~0.05 seconds
        mock_sleep.assert_called_once()

    @patch('papergen.sources.semantic_scholar.time.sleep')
    @patch('papergen.sources.semantic_scholar.time.time')
    def test_rate_limiter_no_wait_needed(self, mock_time, mock_sleep):
        """Test that rate limiter doesn't wait if enough time passed."""
        mock_time.return_value = 1.0

        limiter = RateLimiter(requests_per_second=10.0)
        limiter.last_request_time = 0.0  # Long ago

        limiter.wait_if_needed()

        mock_sleep.assert_not_called()


class TestSemanticScholarClient:
    """Tests for SemanticScholarClient."""

    @pytest.fixture
    def mock_session(self):
        """Create a mocked requests session."""
        with patch('papergen.sources.semantic_scholar.requests.Session') as mock:
            session = Mock()
            mock.return_value = session
            yield session

    @pytest.fixture
    def client(self, mock_session):
        """Create a client with mocked session."""
        return SemanticScholarClient()

    def test_client_initialization(self, mock_session):
        """Test client initialization."""
        client = SemanticScholarClient()

        assert client.api_key is None
        assert client.rate_limiter is not None

    def test_client_with_api_key(self, mock_session):
        """Test client initialization with API key."""
        client = SemanticScholarClient(api_key="test-key")

        assert client.api_key == "test-key"
        assert client.headers["x-api-key"] == "test-key"

    def test_client_custom_rate_limit(self, mock_session):
        """Test client with custom rate limit."""
        client = SemanticScholarClient(rate_limit=5.0)

        assert client.rate_limiter.min_interval == 0.2

    def test_search_papers(self, client, mock_session):
        """Test paper search."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {
                    "paperId": "paper1",
                    "title": "First Paper",
                    "year": 2023,
                    "authors": [],
                    "citationCount": 10,
                    "referenceCount": 5,
                    "influentialCitationCount": 2
                },
                {
                    "paperId": "paper2",
                    "title": "Second Paper",
                    "year": 2022,
                    "authors": [],
                    "citationCount": 20,
                    "referenceCount": 8,
                    "influentialCitationCount": 5
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response

        papers = client.search_papers("machine learning", limit=10)

        assert len(papers) == 2
        assert papers[0].title == "First Paper"
        assert papers[1].title == "Second Paper"
        mock_session.get.assert_called_once()

    def test_search_papers_with_filters(self, client, mock_session):
        """Test paper search with filters."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response

        client.search_papers(
            query="deep learning",
            limit=20,
            year="2022-2023",
            fields_of_study=["Computer Science"],
            min_citation_count=50
        )

        call_args = mock_session.get.call_args
        params = call_args.kwargs["params"]

        assert params["query"] == "deep learning"
        assert params["limit"] == 20
        assert params["year"] == "2022-2023"
        assert params["minCitationCount"] == 50

    def test_get_paper_by_id(self, client, mock_session):
        """Test getting paper by ID."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "paperId": "specific123",
            "title": "Specific Paper",
            "year": 2024,
            "authors": [{"name": "Author"}],
            "citationCount": 100,
            "referenceCount": 50,
            "influentialCitationCount": 20
        }
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response

        paper = client.get_paper_by_id("specific123")

        assert paper is not None
        assert paper.paper_id == "specific123"
        assert paper.title == "Specific Paper"

    def test_get_paper_by_id_not_found(self, client, mock_session):
        """Test getting nonexistent paper."""
        mock_session.get.side_effect = Exception("Not found")

        paper = client.get_paper_by_id("nonexistent")

        assert paper is None

    def test_get_paper_citations(self, client, mock_session):
        """Test getting paper citations."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {"citingPaper": {"paperId": "cite1", "title": "Citing Paper 1"}},
                {"citingPaper": {"paperId": "cite2", "title": "Citing Paper 2"}}
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response

        citations = client.get_paper_citations("paper123")

        assert len(citations) == 2
        assert citations[0].paper_id == "cite1"

    def test_get_paper_references(self, client, mock_session):
        """Test getting paper references."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {"citedPaper": {"paperId": "ref1", "title": "Referenced Paper 1"}},
                {"citedPaper": {"paperId": "ref2", "title": "Referenced Paper 2"}}
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response

        references = client.get_paper_references("paper123")

        assert len(references) == 2
        assert references[0].paper_id == "ref1"

    def test_get_recommended_papers(self, client, mock_session):
        """Test getting paper recommendations."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "recommendedPapers": [
                {"paperId": "rec1", "title": "Recommended 1"},
                {"paperId": "rec2", "title": "Recommended 2"}
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response

        recommendations = client.get_recommended_papers("paper123", limit=5)

        assert len(recommendations) == 2
        assert recommendations[0].paper_id == "rec1"

    def test_search_authors(self, client, mock_session):
        """Test author search."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {"authorId": "auth1", "name": "John Smith", "paperCount": 50},
                {"authorId": "auth2", "name": "John Doe", "paperCount": 30}
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response

        authors = client.search_authors("John", limit=10)

        assert len(authors) == 2
        assert authors[0]["name"] == "John Smith"

    def test_get_author_papers(self, client, mock_session):
        """Test getting papers by author."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {"paperId": "p1", "title": "Paper 1"},
                {"paperId": "p2", "title": "Paper 2"}
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response

        papers = client.get_author_papers("author123")

        assert len(papers) == 2

    def test_rate_limit_retry(self, client, mock_session):
        """Test rate limit handling with retry."""
        # First call returns 429, second succeeds
        rate_limit_response = Mock()
        rate_limit_response.status_code = 429
        rate_limit_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=rate_limit_response
        )

        success_response = Mock()
        success_response.json.return_value = {"data": []}
        success_response.raise_for_status = Mock()

        mock_session.get.side_effect = [rate_limit_response, success_response]

        with patch('papergen.sources.semantic_scholar.time.sleep'):
            papers = client.search_papers("test")

        assert papers == []
        assert mock_session.get.call_count == 2

    def test_find_seminal_papers(self, client, mock_session):
        """Test finding seminal papers."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {"paperId": "s1", "title": "Seminal 1", "citationCount": 1000},
                {"paperId": "s2", "title": "Seminal 2", "citationCount": 500}
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response

        papers = client.find_seminal_papers("deep learning", min_citations=100)

        # Should be sorted by citation count
        assert len(papers) == 2


class TestSemanticScholarClientAnalysis:
    """Tests for analysis methods."""

    @pytest.fixture
    def client_with_mocks(self):
        """Create client with mocked methods."""
        with patch('papergen.sources.semantic_scholar.requests.Session'):
            client = SemanticScholarClient()

            # Mock methods
            client.get_paper_by_id = Mock(return_value=Paper(
                paper_id="test",
                title="Test Paper",
                year=2020,
                authors=[],
                abstract="Abstract",
                citation_count=100,
                reference_count=50,
                influential_citation_count=20,
                venue="Test",
                url="http://test.com",
                arxiv_id=None,
                doi=None,
                fields_of_study=[]
            ))

            client.get_paper_citations = Mock(return_value=[
                Paper(paper_id=f"cite{i}", title=f"Citing {i}", year=2021,
                      authors=[], abstract=None, citation_count=i*10,
                      reference_count=5, influential_citation_count=i,
                      venue=None, url=None, arxiv_id=None, doi=None,
                      fields_of_study=[])
                for i in range(5)
            ])

            client.get_paper_references = Mock(return_value=[
                Paper(paper_id=f"ref{i}", title=f"Reference {i}", year=2019,
                      authors=[], abstract=None, citation_count=i*20,
                      reference_count=10, influential_citation_count=i*2,
                      venue=None, url=None, arxiv_id=None, doi=None,
                      fields_of_study=[])
                for i in range(3)
            ])

            yield client

    def test_analyze_citation_graph(self, client_with_mocks):
        """Test citation graph analysis."""
        analysis = client_with_mocks.analyze_citation_graph("test123")

        assert "paper" in analysis
        assert "total_citations" in analysis
        assert "total_references" in analysis
        assert "top_citing_papers" in analysis
        assert "top_referenced_papers" in analysis
        assert "citation_velocity" in analysis

        assert analysis["total_citations"] == 5
        assert analysis["total_references"] == 3

    def test_analyze_citation_graph_paper_not_found(self, client_with_mocks):
        """Test analysis when paper not found."""
        client_with_mocks.get_paper_by_id = Mock(return_value=None)

        analysis = client_with_mocks.analyze_citation_graph("nonexistent")

        assert analysis == {}

    def test_estimate_citation_velocity(self, client_with_mocks):
        """Test citation velocity estimation."""
        paper = Paper(
            paper_id="test",
            title="Test",
            year=2020,
            authors=[],
            abstract=None,
            citation_count=100,
            reference_count=0,
            influential_citation_count=0,
            venue=None,
            url=None,
            arxiv_id=None,
            doi=None,
            fields_of_study=[]
        )

        current_year = datetime.now().year
        expected_years = current_year - 2020
        expected_velocity = 100 / expected_years

        velocity = client_with_mocks._estimate_citation_velocity(paper, [])

        assert abs(velocity - expected_velocity) < 0.1

    def test_estimate_citation_velocity_no_year(self, client_with_mocks):
        """Test velocity when paper has no year."""
        paper = Paper(
            paper_id="test",
            title="Test",
            year=None,
            authors=[],
            abstract=None,
            citation_count=100,
            reference_count=0,
            influential_citation_count=0,
            venue=None,
            url=None,
            arxiv_id=None,
            doi=None,
            fields_of_study=[]
        )

        velocity = client_with_mocks._estimate_citation_velocity(paper, [])

        assert velocity == 0.0

    def test_get_paper_recommendations_batch(self, client_with_mocks):
        """Test batch recommendations."""
        client_with_mocks.get_recommended_papers = Mock(return_value=[
            Paper(paper_id="rec1", title="Rec", year=2023, authors=[],
                  abstract=None, citation_count=10, reference_count=5,
                  influential_citation_count=2, venue=None, url=None,
                  arxiv_id=None, doi=None, fields_of_study=[])
        ])

        recs = client_with_mocks.get_paper_recommendations_batch(
            ["p1", "p2", "p3"],
            limit_per_paper=5
        )

        assert len(recs) == 3
        assert "p1" in recs
        assert len(recs["p1"]) == 1

    def test_get_paper_recommendations_batch_with_failure(self, client_with_mocks):
        """Test batch recommendations with some failures."""
        def mock_recs(paper_id, limit=5):
            if paper_id == "fail":
                raise Exception("API error")
            return []

        client_with_mocks.get_recommended_papers = Mock(side_effect=mock_recs)

        recs = client_with_mocks.get_paper_recommendations_batch(
            ["ok", "fail", "ok2"],
            limit_per_paper=5
        )

        assert recs["ok"] == []
        assert recs["fail"] == []  # Should be empty on failure
        assert recs["ok2"] == []
