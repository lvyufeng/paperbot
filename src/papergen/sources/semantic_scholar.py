"""Semantic Scholar API integration for research discovery."""

import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..core.logging_config import get_logger


@dataclass
class Paper:
    """Represents a paper from Semantic Scholar."""

    paper_id: str
    title: str
    year: Optional[int]
    authors: List[Dict[str, Any]]
    abstract: Optional[str]
    citation_count: int
    reference_count: int
    influential_citation_count: int
    venue: Optional[str]
    url: Optional[str]
    arxiv_id: Optional[str]
    doi: Optional[str]
    fields_of_study: List[str]

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> 'Paper':
        """Create Paper from API response."""
        return cls(
            paper_id=data.get('paperId', ''),
            title=data.get('title', ''),
            year=data.get('year'),
            authors=data.get('authors', []),
            abstract=data.get('abstract'),
            citation_count=data.get('citationCount', 0),
            reference_count=data.get('referenceCount', 0),
            influential_citation_count=data.get('influentialCitationCount', 0),
            venue=data.get('venue'),
            url=data.get('url'),
            arxiv_id=data.get('externalIds', {}).get('ArXiv'),
            doi=data.get('externalIds', {}).get('DOI'),
            fields_of_study=data.get('fieldsOfStudy', [])
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'paper_id': self.paper_id,
            'title': self.title,
            'year': self.year,
            'authors': [a.get('name', '') for a in self.authors],
            'abstract': self.abstract,
            'citation_count': self.citation_count,
            'reference_count': self.reference_count,
            'influential_citation_count': self.influential_citation_count,
            'venue': self.venue,
            'url': self.url,
            'arxiv_id': self.arxiv_id,
            'doi': self.doi,
            'fields_of_study': self.fields_of_study
        }


class RateLimiter:
    """Simple rate limiter for API requests."""

    def __init__(self, requests_per_second: float = 10.0):
        """
        Initialize rate limiter.

        Args:
            requests_per_second: Maximum requests per second
        """
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0.0

    def wait_if_needed(self):
        """Wait if necessary to respect rate limit."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_interval:
            sleep_time = self.min_interval - time_since_last
            time.sleep(sleep_time)

        self.last_request_time = time.time()


class SemanticScholarClient:
    """Client for Semantic Scholar API with comprehensive features."""

    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    # Available fields for paper queries
    PAPER_FIELDS = [
        'paperId', 'title', 'abstract', 'year', 'authors', 'venue',
        'citationCount', 'referenceCount', 'influentialCitationCount',
        'fieldsOfStudy', 'url', 'externalIds', 'publicationDate',
        'citationStyles', 'embedding'
    ]

    def __init__(self, api_key: Optional[str] = None, rate_limit: float = 10.0):
        """
        Initialize Semantic Scholar client.

        Args:
            api_key: Optional API key for higher rate limits
            rate_limit: Requests per second (default: 10 for free tier)
        """
        self.logger = get_logger()
        self.api_key = api_key
        self.rate_limiter = RateLimiter(rate_limit)

        # Setup session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set headers
        self.headers = {}
        if api_key:
            self.headers['x-api-key'] = api_key

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make API request with rate limiting and error handling.

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            API response data
        """
        self.rate_limiter.wait_if_needed()

        url = f"{self.BASE_URL}/{endpoint}"

        try:
            response = self.session.get(
                url,
                params=params,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                self.logger.warning("Rate limit exceeded, waiting 60 seconds...")
                time.sleep(60)
                return self._make_request(endpoint, params)
            else:
                self.logger.error(f"HTTP error: {e}")
                raise

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {e}")
            raise

    def search_papers(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0,
        year: Optional[str] = None,
        fields_of_study: Optional[List[str]] = None,
        venue: Optional[List[str]] = None,
        min_citation_count: Optional[int] = None
    ) -> List[Paper]:
        """
        Search for papers by query.

        Args:
            query: Search query
            limit: Maximum number of results (max 100)
            offset: Pagination offset
            year: Year filter (e.g., "2020", "2020-2023")
            fields_of_study: Filter by fields (e.g., ["Computer Science"])
            venue: Filter by venue
            min_citation_count: Minimum citation count

        Returns:
            List of Paper objects
        """
        self.logger.info(f"Searching papers: {query}")

        params = {
            'query': query,
            'limit': min(limit, 100),
            'offset': offset,
            'fields': ','.join(self.PAPER_FIELDS)
        }

        if year:
            params['year'] = year
        if fields_of_study:
            params['fieldsOfStudy'] = ','.join(fields_of_study)
        if venue:
            params['venue'] = ','.join(venue)
        if min_citation_count:
            params['minCitationCount'] = min_citation_count

        data = self._make_request('paper/search', params)
        papers = [Paper.from_api_response(p) for p in data.get('data', [])]

        self.logger.info(f"Found {len(papers)} papers")
        return papers

    def get_paper_by_id(self, paper_id: str) -> Optional[Paper]:
        """
        Get paper details by Semantic Scholar ID.

        Args:
            paper_id: Paper ID (can be S2 ID, DOI, ArXiv ID, etc.)

        Returns:
            Paper object or None
        """
        self.logger.info(f"Fetching paper: {paper_id}")

        params = {'fields': ','.join(self.PAPER_FIELDS)}

        try:
            data = self._make_request(f'paper/{paper_id}', params)
            return Paper.from_api_response(data)
        except Exception as e:
            self.logger.error(f"Failed to fetch paper {paper_id}: {e}")
            return None

    def get_paper_citations(
        self,
        paper_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Paper]:
        """
        Get papers that cite this paper.

        Args:
            paper_id: Paper ID
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of citing papers
        """
        self.logger.info(f"Fetching citations for: {paper_id}")

        params = {
            'limit': min(limit, 1000),
            'offset': offset,
            'fields': ','.join(self.PAPER_FIELDS)
        }

        data = self._make_request(f'paper/{paper_id}/citations', params)
        papers = [Paper.from_api_response(c['citingPaper']) for c in data.get('data', [])]

        self.logger.info(f"Found {len(papers)} citing papers")
        return papers

    def get_paper_references(
        self,
        paper_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Paper]:
        """
        Get papers referenced by this paper.

        Args:
            paper_id: Paper ID
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of referenced papers
        """
        self.logger.info(f"Fetching references for: {paper_id}")

        params = {
            'limit': min(limit, 1000),
            'offset': offset,
            'fields': ','.join(self.PAPER_FIELDS)
        }

        data = self._make_request(f'paper/{paper_id}/references', params)
        papers = [Paper.from_api_response(r['citedPaper']) for r in data.get('data', [])]

        self.logger.info(f"Found {len(papers)} referenced papers")
        return papers

    def get_recommended_papers(
        self,
        paper_id: str,
        limit: int = 10,
        fields: Optional[List[str]] = None
    ) -> List[Paper]:
        """
        Get recommended papers based on a paper.

        Args:
            paper_id: Paper ID
            limit: Maximum number of recommendations
            fields: Optional list of fields to include

        Returns:
            List of recommended papers
        """
        self.logger.info(f"Getting recommendations for: {paper_id}")

        if fields is None:
            fields = self.PAPER_FIELDS

        params = {
            'limit': min(limit, 100),
            'fields': ','.join(fields)
        }

        data = self._make_request(f'recommendations/v1/papers/forpaper/{paper_id}', params)
        papers = [Paper.from_api_response(p) for p in data.get('recommendedPapers', [])]

        self.logger.info(f"Found {len(papers)} recommended papers")
        return papers

    def search_authors(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for authors.

        Args:
            query: Author name query
            limit: Maximum number of results

        Returns:
            List of author information
        """
        self.logger.info(f"Searching authors: {query}")

        params = {
            'query': query,
            'limit': min(limit, 100),
            'fields': 'authorId,name,paperCount,citationCount,hIndex'
        }

        data = self._make_request('author/search', params)
        authors = data.get('data', [])

        self.logger.info(f"Found {len(authors)} authors")
        return authors

    def get_author_papers(
        self,
        author_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Paper]:
        """
        Get papers by an author.

        Args:
            author_id: Author ID
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of papers
        """
        self.logger.info(f"Fetching papers for author: {author_id}")

        params = {
            'limit': min(limit, 1000),
            'offset': offset,
            'fields': ','.join(self.PAPER_FIELDS)
        }

        data = self._make_request(f'author/{author_id}/papers', params)
        papers = [Paper.from_api_response(p) for p in data.get('data', [])]

        self.logger.info(f"Found {len(papers)} papers")
        return papers

    def get_trending_papers(
        self,
        field: str = "computer-science",
        limit: int = 10
    ) -> List[Paper]:
        """
        Get trending papers in a field (papers with recent high citation velocity).

        Args:
            field: Field of study
            limit: Maximum number of results

        Returns:
            List of trending papers
        """
        # Note: This uses search with recent year filter and sorts by citations
        current_year = datetime.now().year
        year_range = f"{current_year-1}-{current_year}"

        return self.search_papers(
            query=field,
            limit=limit,
            year=year_range,
            min_citation_count=10
        )

    def analyze_citation_graph(
        self,
        paper_id: str,
        depth: int = 1
    ) -> Dict[str, Any]:
        """
        Analyze citation graph around a paper.

        Args:
            paper_id: Paper ID
            depth: How many levels to explore (1 or 2)

        Returns:
            Citation graph analysis
        """
        self.logger.info(f"Analyzing citation graph for: {paper_id}")

        # Get the paper
        paper = self.get_paper_by_id(paper_id)
        if not paper:
            return {}

        # Get citations and references
        citations = self.get_paper_citations(paper_id, limit=50)
        references = self.get_paper_references(paper_id, limit=50)

        # Sort by influence
        top_citations = sorted(
            citations,
            key=lambda p: p.influential_citation_count,
            reverse=True
        )[:10]

        top_references = sorted(
            references,
            key=lambda p: p.citation_count,
            reverse=True
        )[:10]

        return {
            'paper': paper.to_dict(),
            'total_citations': len(citations),
            'total_references': len(references),
            'top_citing_papers': [p.to_dict() for p in top_citations],
            'top_referenced_papers': [p.to_dict() for p in top_references],
            'citation_velocity': self._estimate_citation_velocity(paper, citations),
            'influential_citations': paper.influential_citation_count
        }

    def _estimate_citation_velocity(
        self,
        paper: Paper,
        citations: List[Paper]
    ) -> float:
        """
        Estimate citation velocity (citations per year).

        Args:
            paper: The paper
            citations: List of citing papers

        Returns:
            Citations per year
        """
        if not paper.year:
            return 0.0

        current_year = datetime.now().year
        years_since_publication = max(current_year - paper.year, 1)

        return paper.citation_count / years_since_publication

    def find_seminal_papers(
        self,
        query: str,
        min_citations: int = 100,
        limit: int = 20
    ) -> List[Paper]:
        """
        Find seminal/foundational papers in a field.

        Args:
            query: Research area query
            min_citations: Minimum citation count
            limit: Maximum number of results

        Returns:
            List of highly-cited papers
        """
        self.logger.info(f"Finding seminal papers for: {query}")

        papers = self.search_papers(
            query=query,
            limit=limit,
            min_citation_count=min_citations
        )

        # Sort by citation count
        seminal = sorted(papers, key=lambda p: p.citation_count, reverse=True)

        return seminal

    def get_paper_recommendations_batch(
        self,
        paper_ids: List[str],
        limit_per_paper: int = 5
    ) -> Dict[str, List[Paper]]:
        """
        Get recommendations for multiple papers.

        Args:
            paper_ids: List of paper IDs
            limit_per_paper: Recommendations per paper

        Returns:
            Dictionary mapping paper_id to recommendations
        """
        recommendations = {}

        for paper_id in paper_ids:
            try:
                recs = self.get_recommended_papers(paper_id, limit=limit_per_paper)
                recommendations[paper_id] = recs
            except Exception as e:
                self.logger.error(f"Failed to get recommendations for {paper_id}: {e}")
                recommendations[paper_id] = []

        return recommendations
