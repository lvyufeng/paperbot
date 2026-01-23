"""Unit tests for custom exceptions."""

import pytest
from papergen.core.exceptions import (
    PaperGenException,
    ProjectNotFoundError,
    ProjectAlreadyExistsError,
    ProjectStateError,
    APIAuthenticationError,
    APIRateLimitError,
    APIConnectionError,
    APITimeoutError,
    PDFExtractionError,
    WebExtractionError,
    EmptyContentError,
    InvalidConfigError,
    map_http_status_to_exception
)


class TestExceptionHierarchy:
    """Test exception hierarchy and inheritance."""

    def test_base_exception(self):
        """Test base PaperGenException."""
        exc = PaperGenException("Test error")
        assert str(exc) == "Test error"
        assert isinstance(exc, Exception)

    def test_project_exceptions_inherit_from_base(self):
        """Test project exceptions inherit from PaperGenException."""
        exc = ProjectNotFoundError("/path/to/project")
        assert isinstance(exc, PaperGenException)
        assert "/path/to/project" in str(exc)

    def test_api_exceptions_inherit_from_base(self):
        """Test API exceptions inherit from PaperGenException."""
        exc = APIAuthenticationError("Claude")
        assert isinstance(exc, PaperGenException)
        assert "Claude" in str(exc)


class TestProjectExceptions:
    """Test project-related exceptions."""

    def test_project_not_found_error(self):
        """Test ProjectNotFoundError."""
        path = "/path/to/project"
        exc = ProjectNotFoundError(path)

        assert exc.path == path
        assert path in str(exc)
        assert "project" in str(exc).lower()
        assert "found" in str(exc).lower()

    def test_project_already_exists_error(self):
        """Test ProjectAlreadyExistsError."""
        path = "/existing/project"
        exc = ProjectAlreadyExistsError(path)

        assert exc.path == path
        assert path in str(exc)
        assert "already exists" in str(exc).lower()

    def test_project_state_error(self):
        """Test ProjectStateError."""
        message = "State file corrupted"
        exc = ProjectStateError(message)

        assert message in str(exc)


class TestAPIExceptions:
    """Test API-related exceptions."""

    def test_api_authentication_error(self):
        """Test APIAuthenticationError."""
        provider = "Claude"
        exc = APIAuthenticationError(provider)

        assert exc.provider == provider
        assert provider in str(exc)
        assert "authentication" in str(exc).lower()
        assert "api key" in str(exc).lower()

    def test_api_rate_limit_error(self):
        """Test APIRateLimitError."""
        provider = "Claude"
        retry_after = 60
        exc = APIRateLimitError(provider, retry_after)

        assert exc.provider == provider
        assert exc.retry_after == retry_after
        assert provider in str(exc)
        assert "60" in str(exc)

    def test_api_rate_limit_error_without_retry(self):
        """Test APIRateLimitError without retry_after."""
        exc = APIRateLimitError("Claude")
        assert exc.retry_after is None
        assert "rate limit" in str(exc).lower()

    def test_api_connection_error(self):
        """Test APIConnectionError."""
        provider = "Claude"
        message = "Connection timeout"
        exc = APIConnectionError(provider, message)

        assert exc.provider == provider
        assert provider in str(exc)
        assert message in str(exc)

    def test_api_timeout_error(self):
        """Test APITimeoutError."""
        provider = "Claude"
        timeout = 30
        exc = APITimeoutError(provider, timeout)

        assert exc.provider == provider
        assert exc.timeout == timeout
        assert str(timeout) in str(exc)


class TestExtractionExceptions:
    """Test extraction-related exceptions."""

    def test_pdf_extraction_error(self):
        """Test PDFExtractionError."""
        file_path = "/path/to/paper.pdf"
        reason = "File is corrupted"
        exc = PDFExtractionError(file_path, reason)

        assert exc.file_path == file_path
        assert exc.reason == reason
        assert file_path in str(exc)
        assert reason in str(exc)

    def test_web_extraction_error(self):
        """Test WebExtractionError."""
        url = "https://example.com/paper"
        reason = "404 Not Found"
        exc = WebExtractionError(url, reason)

        assert exc.url == url
        assert exc.reason == reason
        assert url in str(exc)
        assert reason in str(exc)

    def test_empty_content_error(self):
        """Test EmptyContentError."""
        source = "paper.pdf"
        min_length = 100
        exc = EmptyContentError(source, min_length)

        assert exc.source == source
        assert exc.min_length == min_length
        assert source in str(exc)
        assert str(min_length) in str(exc)

    def test_empty_content_error_default_min_length(self):
        """Test EmptyContentError with default min_length."""
        exc = EmptyContentError("paper.pdf")
        assert exc.min_length == 100


class TestConfigurationExceptions:
    """Test configuration-related exceptions."""

    def test_invalid_config_error(self):
        """Test InvalidConfigError."""
        field = "api.model"
        reason = "Invalid model name"
        exc = InvalidConfigError(field, reason)

        assert exc.field == field
        assert exc.reason == reason
        assert field in str(exc)
        assert reason in str(exc)


class TestHTTPStatusMapping:
    """Test HTTP status code to exception mapping."""

    def test_map_401_to_authentication_error(self):
        """Test 401 maps to APIAuthenticationError."""
        exc = map_http_status_to_exception(401, "TestAPI", "Unauthorized")
        assert isinstance(exc, APIAuthenticationError)
        assert exc.provider == "TestAPI"

    def test_map_403_to_authentication_error(self):
        """Test 403 maps to APIAuthenticationError."""
        exc = map_http_status_to_exception(403, "TestAPI", "Forbidden")
        assert isinstance(exc, APIAuthenticationError)

    def test_map_429_to_rate_limit_error(self):
        """Test 429 maps to APIRateLimitError."""
        exc = map_http_status_to_exception(429, "TestAPI", "Too Many Requests")
        assert isinstance(exc, APIRateLimitError)
        assert exc.provider == "TestAPI"

    def test_map_500_to_connection_error(self):
        """Test 500 maps to APIConnectionError."""
        exc = map_http_status_to_exception(500, "TestAPI", "Internal Server Error")
        assert isinstance(exc, APIConnectionError)
        assert "Server error" in str(exc)

    def test_map_502_to_connection_error(self):
        """Test 502 maps to APIConnectionError."""
        exc = map_http_status_to_exception(502, "TestAPI", "Bad Gateway")
        assert isinstance(exc, APIConnectionError)

    def test_map_other_status_to_response_error(self):
        """Test other status codes map to APIResponseError."""
        from papergen.core.exceptions import APIResponseError

        exc = map_http_status_to_exception(400, "TestAPI", "Bad Request")
        assert isinstance(exc, APIResponseError)
        assert exc.status_code == 400
        assert exc.provider == "TestAPI"


class TestExceptionCatching:
    """Test exception catching patterns."""

    def test_catch_specific_exception(self):
        """Test catching specific exception type."""
        with pytest.raises(PDFExtractionError) as exc_info:
            raise PDFExtractionError("test.pdf", "Test error")

        assert exc_info.value.file_path == "test.pdf"
        assert exc_info.value.reason == "Test error"

    def test_catch_base_exception(self):
        """Test catching base PaperGenException."""
        with pytest.raises(PaperGenException):
            raise PDFExtractionError("test.pdf", "Test error")

    def test_exception_attributes_accessible(self):
        """Test exception attributes are accessible."""
        try:
            raise APIRateLimitError("Claude", 60)
        except APIRateLimitError as e:
            assert e.provider == "Claude"
            assert e.retry_after == 60


class TestMissingConfigExceptions:
    """Test configuration missing exceptions."""

    def test_missing_config_error(self):
        """Test MissingConfigError."""
        from papergen.core.exceptions import MissingConfigError

        exc = MissingConfigError("api_key")

        assert exc.field == "api_key"
        assert "api_key" in str(exc)
        assert "missing" in str(exc).lower()

    def test_api_key_not_found_error(self):
        """Test APIKeyNotFoundError."""
        from papergen.core.exceptions import APIKeyNotFoundError

        exc = APIKeyNotFoundError("Claude")

        assert exc.provider == "Claude"
        assert "Claude" in str(exc)
        assert "api key" in str(exc).lower()


class TestSourceExceptions:
    """Test source management exceptions."""

    def test_source_not_found_error(self):
        """Test SourceNotFoundError."""
        from papergen.core.exceptions import SourceNotFoundError

        exc = SourceNotFoundError("source_123")

        assert exc.source_id == "source_123"
        assert "source_123" in str(exc)

    def test_duplicate_source_error(self):
        """Test DuplicateSourceError."""
        from papergen.core.exceptions import DuplicateSourceError

        exc = DuplicateSourceError("source_123")

        assert exc.source_id == "source_123"
        assert "already exists" in str(exc).lower()


class TestDocumentExceptions:
    """Test document generation exceptions."""

    def test_outline_error(self):
        """Test OutlineError."""
        from papergen.core.exceptions import OutlineError

        exc = OutlineError("Invalid section structure")

        assert "Invalid section structure" in str(exc)

    def test_draft_error(self):
        """Test DraftError."""
        from papergen.core.exceptions import DraftError

        exc = DraftError("introduction", "AI generation failed")

        assert exc.section_id == "introduction"
        assert exc.reason == "AI generation failed"
        assert "introduction" in str(exc)

    def test_revision_error(self):
        """Test RevisionError."""
        from papergen.core.exceptions import RevisionError

        exc = RevisionError("methods", "Revision limit exceeded")

        assert exc.section_id == "methods"
        assert exc.reason == "Revision limit exceeded"

    def test_formatting_error(self):
        """Test FormattingError."""
        from papergen.core.exceptions import FormattingError

        exc = FormattingError("latex", "Missing template")

        assert exc.format_type == "latex"
        assert exc.reason == "Missing template"
        assert "latex" in str(exc)


class TestCitationExceptions:
    """Test citation exceptions."""

    def test_invalid_citation_error(self):
        """Test InvalidCitationError."""
        from papergen.core.exceptions import InvalidCitationError

        exc = InvalidCitationError("[Smith 2024]", "Missing author info")

        assert exc.citation == "[Smith 2024]"
        assert exc.reason == "Missing author info"

    def test_citation_not_found_error(self):
        """Test CitationNotFoundError."""
        from papergen.core.exceptions import CitationNotFoundError

        exc = CitationNotFoundError("smith2024")

        assert exc.citation_key == "smith2024"
        assert "smith2024" in str(exc)


class TestValidationExceptions:
    """Test validation exceptions."""

    def test_invalid_input_error(self):
        """Test InvalidInputError."""
        from papergen.core.exceptions import InvalidInputError

        exc = InvalidInputError("topic", "", "Cannot be empty")

        assert exc.field == "topic"
        assert exc.value == ""
        assert exc.reason == "Cannot be empty"

    def test_file_validation_error(self):
        """Test FileValidationError."""
        from papergen.core.exceptions import FileValidationError

        exc = FileValidationError("/path/to/file.pdf", "File too large")

        assert exc.file_path == "/path/to/file.pdf"
        assert exc.reason == "File too large"


class TestDiscoveryExceptions:
    """Test research discovery exceptions."""

    def test_paper_search_error(self):
        """Test PaperSearchError."""
        from papergen.core.exceptions import PaperSearchError

        exc = PaperSearchError("machine learning", "Network timeout")

        assert exc.query == "machine learning"
        assert exc.reason == "Network timeout"

    def test_paper_not_found_error(self):
        """Test PaperNotFoundError."""
        from papergen.core.exceptions import PaperNotFoundError

        exc = PaperNotFoundError("arxiv:2024.12345")

        assert exc.paper_id == "arxiv:2024.12345"
        assert "arxiv:2024.12345" in str(exc)


class TestAPIResponseError:
    """Test APIResponseError."""

    def test_api_response_error(self):
        """Test APIResponseError."""
        from papergen.core.exceptions import APIResponseError

        exc = APIResponseError("Claude", 404, "Not found")

        assert exc.provider == "Claude"
        assert exc.status_code == 404
        assert exc.message == "Not found"
        assert "404" in str(exc)
