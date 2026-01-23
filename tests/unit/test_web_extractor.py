"""Unit tests for web extraction."""

import pytest
from unittest.mock import Mock, patch
from papergen.sources.web_extractor import WebExtractor
from papergen.core.exceptions import WebExtractionError, EmptyContentError


class TestWebExtractor:
    """Test web extraction functionality."""

    def test_extractor_initialization(self):
        """Test WebExtractor initialization."""
        extractor = WebExtractor()
        assert extractor.timeout == 30
        assert extractor.user_agent == "PaperGen/1.0"
        assert extractor.max_retries == 3

    @patch('papergen.sources.web_extractor.requests.get')
    def test_extract_valid_url(self, mock_get):
        """Test extracting content from valid URL."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <head><title>Test Paper</title></head>
            <body>
                <article>
                    <h1>Test Paper Title</h1>
                    <p>This is a test paper with enough content to pass validation.
                    It contains multiple paragraphs and sufficient text to demonstrate
                    the extraction functionality. This ensures we have more than 100
                    characters of content.</p>
                </article>
            </body>
        </html>
        """
        mock_get.return_value = mock_response

        extractor = WebExtractor()
        result = extractor.extract("https://example.com/paper")

        assert "metadata" in result
        assert "content" in result
        assert "citations" in result
        assert len(result["content"]["full_text"]) > 0

    @patch('papergen.sources.web_extractor.requests.get')
    def test_extract_url_with_empty_content_raises_error(self, mock_get):
        """Test extracting URL with empty content raises EmptyContentError."""
        # Mock response with minimal content
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><body><p>Short</p></body></html>"
        mock_get.return_value = mock_response

        extractor = WebExtractor()

        with pytest.raises(EmptyContentError) as exc_info:
            extractor.extract("https://example.com/short")

        assert "example.com" in exc_info.value.source

    @patch('papergen.sources.web_extractor.requests.get')
    def test_extract_url_connection_error(self, mock_get):
        """Test extracting URL with connection error."""
        # Mock connection error
        import requests
        mock_get.side_effect = requests.ConnectionError("Connection failed")

        extractor = WebExtractor()

        with pytest.raises(WebExtractionError) as exc_info:
            extractor.extract("https://example.com/paper")

        assert "example.com" in exc_info.value.url

    @patch('papergen.sources.web_extractor.requests.get')
    def test_extract_url_timeout(self, mock_get):
        """Test extracting URL with timeout."""
        # Mock timeout
        import requests
        mock_get.side_effect = requests.Timeout("Request timed out")

        extractor = WebExtractor()

        with pytest.raises(WebExtractionError):
            extractor.extract("https://example.com/paper")

    @patch('papergen.sources.web_extractor.requests.get')
    def test_extract_url_404_error(self, mock_get):
        """Test extracting URL that returns 404."""
        # Mock 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")
        mock_get.return_value = mock_response

        extractor = WebExtractor()

        with pytest.raises(WebExtractionError):
            extractor.extract("https://example.com/notfound")


class TestWebContentParsing:
    """Test web content parsing."""

    @patch('papergen.sources.web_extractor.requests.get')
    def test_extract_metadata(self, mock_get):
        """Test extracting metadata from web page."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <head>
                <title>Test Paper</title>
                <meta name="author" content="Test Author">
                <meta name="description" content="Test description with enough content">
            </head>
            <body>
                <p>Content with sufficient length to pass validation checks.
                This paragraph contains enough text to ensure we meet the minimum
                character requirement for content extraction.</p>
            </body>
        </html>
        """
        mock_get.return_value = mock_response

        extractor = WebExtractor()
        result = extractor.extract("https://example.com/paper")

        metadata = result["metadata"]
        assert isinstance(metadata, dict)
        assert "url" in metadata

    @patch('papergen.sources.web_extractor.requests.get')
    def test_extract_main_content(self, mock_get):
        """Test extracting main content from web page."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <body>
                <article>
                    <h1>Main Title</h1>
                    <p>This is the main content of the article. It contains
                    sufficient text to pass validation. We need to ensure that
                    the extracted content meets the minimum length requirements.</p>
                </article>
            </body>
        </html>
        """
        mock_get.return_value = mock_response

        extractor = WebExtractor()
        result = extractor.extract("https://example.com/paper")

        content = result["content"]
        assert "full_text" in content
        assert len(content["full_text"]) > 0


class TestWebExtractionRetry:
    """Test web extraction retry logic."""

    @patch('papergen.sources.web_extractor.requests.get')
    def test_retry_on_temporary_failure(self, mock_get):
        """Test retry logic on temporary failures."""
        # This would test the retry mechanism
        # For now, we verify the max_retries setting
        extractor = WebExtractor()
        assert extractor.max_retries == 3

    @patch('papergen.sources.web_extractor.requests.get')
    def test_retry_succeeds_after_failures(self, mock_get):
        """Test retry succeeds after initial failures."""
        import requests

        # First two calls fail, third succeeds
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <body>
                <article>
                    <p>This is the main content with enough text to pass validation.
                    We need over 100 characters here to ensure extraction succeeds.</p>
                </article>
            </body>
        </html>
        """

        mock_get.side_effect = [
            requests.RequestException("Error 1"),
            requests.RequestException("Error 2"),
            mock_response
        ]

        extractor = WebExtractor()
        result = extractor.extract("https://example.com/paper")

        assert "content" in result
        assert mock_get.call_count == 3


class TestArxivExtraction:
    """Test arXiv-specific extraction."""

    @patch('papergen.sources.web_extractor.requests.get')
    def test_extract_arxiv_metadata(self, mock_get):
        """Test extracting metadata from arXiv page."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <head><title>arXiv Paper</title></head>
            <body>
                <div class="authors">
                    <a href="/author/1">John Smith</a>
                    <a href="/author/2">Jane Doe</a>
                </div>
                <blockquote class="abstract">
                    Abstract: This is the abstract of the paper with enough text
                    to pass validation. It describes the research methodology and
                    findings in sufficient detail.
                </blockquote>
                <div id="content">
                    <p>Full paper content with sufficient length to pass validation.
                    This paragraph ensures we meet the minimum character requirements
                    for the web extraction process.</p>
                </div>
            </body>
        </html>
        """
        mock_get.return_value = mock_response

        extractor = WebExtractor()
        result = extractor.extract("https://arxiv.org/abs/1234.5678")

        metadata = result["metadata"]
        assert "John Smith" in metadata.get("authors", [])
        assert "Jane Doe" in metadata.get("authors", [])

    @patch('papergen.sources.web_extractor.requests.get')
    def test_extract_arxiv_abstract(self, mock_get):
        """Test extracting abstract from arXiv page."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <body>
                <blockquote class="abstract">
                    Abstract: This is a detailed research abstract with sufficient text.
                </blockquote>
                <div id="content">
                    <p>Main content with enough characters to pass the 100 char minimum.
                    We need to include additional text here for validation purposes.</p>
                </div>
            </body>
        </html>
        """
        mock_get.return_value = mock_response

        extractor = WebExtractor()
        result = extractor.extract("https://arxiv.org/abs/9999.1234")

        metadata = result["metadata"]
        assert "abstract" in metadata
        assert "detailed research abstract" in metadata["abstract"]


class TestSectionParsing:
    """Test section parsing functionality."""

    @patch('papergen.sources.web_extractor.requests.get')
    def test_parse_sections_with_headings(self, mock_get):
        """Test parsing sections from HTML with headings."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <body>
                <article>
                    <h1>Introduction</h1>
                    <p>Introduction content with enough text to pass validation
                    requirements for the extraction process.</p>
                    <h2>Methods</h2>
                    <p>Methods content describing the research methodology used.</p>
                    <h2>Results</h2>
                    <p>Results content presenting the findings of the study.</p>
                    <h3>Discussion</h3>
                    <p>Discussion of the implications and significance.</p>
                </article>
            </body>
        </html>
        """
        mock_get.return_value = mock_response

        extractor = WebExtractor()
        result = extractor.extract("https://example.com/paper")

        sections = result["content"]["sections"]
        assert len(sections) > 0
        section_titles = [s["title"] for s in sections]
        assert "Introduction" in section_titles

    @patch('papergen.sources.web_extractor.requests.get')
    def test_parse_sections_limit(self, mock_get):
        """Test that section parsing limits to 20 sections."""
        # Create HTML with many headings
        headings = "\n".join([f"<h2>Section {i}</h2><p>Content {i}</p>" for i in range(30)])
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = f"""
        <html>
            <body>
                <article>
                    {headings}
                </article>
            </body>
        </html>
        """
        mock_get.return_value = mock_response

        extractor = WebExtractor()
        result = extractor.extract("https://example.com/paper")

        sections = result["content"]["sections"]
        assert len(sections) <= 20


class TestCitationExtraction:
    """Test citation extraction functionality."""

    @patch('papergen.sources.web_extractor.requests.get')
    def test_extract_citations_basic(self, mock_get):
        """Test extracting basic citation patterns."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <body>
                <article>
                    <p>According to Smith, 2020, this approach is valid.
                    As noted by Johnson et al., 2019, the results are significant.
                    Previous work by Williams 2018 showed similar findings.
                    This content has enough text to pass the validation checks.</p>
                </article>
            </body>
        </html>
        """
        mock_get.return_value = mock_response

        extractor = WebExtractor()
        result = extractor.extract("https://example.com/paper")

        citations = result["citations"]
        assert len(citations) > 0

        # Check citation structure
        for citation in citations:
            assert "text" in citation
            assert "author" in citation
            assert "year" in citation
            assert "context" in citation

    @patch('papergen.sources.web_extractor.requests.get')
    def test_extract_citations_et_al(self, mock_get):
        """Test extracting 'et al.' citations."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <body>
                <article>
                    <p>Research by Johnson et al., 2021 demonstrates this effect.
                    Additional work by Brown et al. 2020 confirms these findings.
                    This paragraph has enough content for extraction validation.</p>
                </article>
            </body>
        </html>
        """
        mock_get.return_value = mock_response

        extractor = WebExtractor()
        result = extractor.extract("https://example.com/paper")

        citations = result["citations"]
        et_al_citations = [c for c in citations if "et al" in c["author"]]
        assert len(et_al_citations) > 0

    @patch('papergen.sources.web_extractor.requests.get')
    def test_extract_citations_limit(self, mock_get):
        """Test that citation extraction limits to 100."""
        # Create text with many citations
        citations_text = " ".join([f"Smith{i}, 2020" for i in range(150)])
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = f"""
        <html>
            <body>
                <article>
                    <p>{citations_text}</p>
                </article>
            </body>
        </html>
        """
        mock_get.return_value = mock_response

        extractor = WebExtractor()
        result = extractor.extract("https://example.com/paper")

        citations = result["citations"]
        assert len(citations) <= 100


class TestContentContainerDetection:
    """Test content container detection."""

    @patch('papergen.sources.web_extractor.requests.get')
    def test_detect_content_by_id(self, mock_get):
        """Test detecting content by ID selector."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <body>
                <nav>Navigation content that should be ignored</nav>
                <div id="content">
                    <p>This is the main content identified by ID selector.
                    It has sufficient length to pass all validation checks.</p>
                </div>
                <footer>Footer content to ignore</footer>
            </body>
        </html>
        """
        mock_get.return_value = mock_response

        extractor = WebExtractor()
        result = extractor.extract("https://example.com/paper")

        # Navigation and footer should not be in content
        assert "Navigation" not in result["content"]["full_text"]

    @patch('papergen.sources.web_extractor.requests.get')
    def test_detect_content_by_class(self, mock_get):
        """Test detecting content by class selector."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <body>
                <div class="sidebar">Sidebar to ignore</div>
                <div class="main-content">
                    <p>This is the main content identified by class selector.
                    It contains enough text to pass the extraction validation.</p>
                </div>
            </body>
        </html>
        """
        mock_get.return_value = mock_response

        extractor = WebExtractor()
        result = extractor.extract("https://example.com/paper")

        assert "main content" in result["content"]["full_text"].lower()

    @patch('papergen.sources.web_extractor.requests.get')
    def test_detect_content_by_role(self, mock_get):
        """Test detecting content by role attribute."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <body>
                <div role="main">
                    <p>This is the main content identified by role attribute.
                    It has enough characters to satisfy validation requirements.</p>
                </div>
            </body>
        </html>
        """
        mock_get.return_value = mock_response

        extractor = WebExtractor()
        result = extractor.extract("https://example.com/paper")

        assert "content" in result

    @patch('papergen.sources.web_extractor.requests.get')
    def test_fallback_to_body(self, mock_get):
        """Test fallback to body when no main content found."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <body>
                <p>This is content in body with no semantic containers.
                It needs to have enough text to pass extraction validation
                and meet the minimum character requirements.</p>
            </body>
        </html>
        """
        mock_get.return_value = mock_response

        extractor = WebExtractor()
        result = extractor.extract("https://example.com/paper")

        assert "content" in result
        assert len(result["content"]["full_text"]) > 0


class TestMetadataExtraction:
    """Test metadata extraction methods."""

    @patch('papergen.sources.web_extractor.requests.get')
    def test_extract_og_title(self, mock_get):
        """Test extracting Open Graph title."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <head>
                <title>Regular Title</title>
                <meta property="og:title" content="Open Graph Title">
            </head>
            <body>
                <p>Content with sufficient length to pass extraction validation.
                This paragraph ensures we meet the minimum requirements.</p>
            </body>
        </html>
        """
        mock_get.return_value = mock_response

        extractor = WebExtractor()
        result = extractor.extract("https://example.com/paper")

        assert result["metadata"]["title"] == "Open Graph Title"

    @patch('papergen.sources.web_extractor.requests.get')
    def test_extract_author_meta(self, mock_get):
        """Test extracting author from meta tag."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <head>
                <title>Test Paper</title>
                <meta name="author" content="John Doe, Jane Smith">
            </head>
            <body>
                <p>Content with enough text to pass validation requirements.
                Additional text to meet the minimum character threshold.</p>
            </body>
        </html>
        """
        mock_get.return_value = mock_response

        extractor = WebExtractor()
        result = extractor.extract("https://example.com/paper")

        authors = result["metadata"]["authors"]
        assert "John Doe" in authors
        assert "Jane Smith" in authors


class TestFetchURL:
    """Test URL fetching functionality."""

    @patch('papergen.sources.web_extractor.requests.get')
    def test_fetch_url_success(self, mock_get):
        """Test successful URL fetch."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "HTML content"
        mock_get.return_value = mock_response

        extractor = WebExtractor()
        result = extractor._fetch_url("https://example.com")

        assert result == "HTML content"
        mock_get.assert_called_once()

    @patch('papergen.sources.web_extractor.requests.get')
    def test_fetch_url_all_retries_fail(self, mock_get):
        """Test URL fetch when all retries fail."""
        import requests
        mock_get.side_effect = requests.RequestException("Connection error")

        extractor = WebExtractor()
        result = extractor._fetch_url("https://example.com")

        assert result is None
        assert mock_get.call_count == 3  # max_retries

    @patch('papergen.sources.web_extractor.requests.get')
    def test_fetch_url_custom_user_agent(self, mock_get):
        """Test that custom user agent is sent."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Content"
        mock_get.return_value = mock_response

        extractor = WebExtractor()
        extractor._fetch_url("https://example.com")

        call_kwargs = mock_get.call_args[1]
        assert "User-Agent" in call_kwargs["headers"]
        assert call_kwargs["headers"]["User-Agent"] == "PaperGen/1.0"


class TestContentLimits:
    """Test content length limits."""

    @patch('papergen.sources.web_extractor.requests.get')
    def test_content_truncated_to_50k(self, mock_get):
        """Test that content is truncated to 50000 chars."""
        large_content = "x" * 60000
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = f"""
        <html>
            <body>
                <article>
                    <p>{large_content}</p>
                </article>
            </body>
        </html>
        """
        mock_get.return_value = mock_response

        extractor = WebExtractor()
        result = extractor.extract("https://example.com/paper")

        assert len(result["content"]["full_text"]) <= 50000

    @patch('papergen.sources.web_extractor.requests.get')
    def test_section_content_truncated(self, mock_get):
        """Test that section content is truncated to 2000 chars."""
        large_section = "x" * 3000
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = f"""
        <html>
            <body>
                <article>
                    <h1>Section Title</h1>
                    <p>{large_section}</p>
                    <p>Additional padding content for validation checks.</p>
                </article>
            </body>
        </html>
        """
        mock_get.return_value = mock_response

        extractor = WebExtractor()
        result = extractor.extract("https://example.com/paper")

        for section in result["content"]["sections"]:
            assert len(section["text"]) <= 2000
