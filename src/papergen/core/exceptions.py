"""Custom exceptions for PaperGen.

This module defines a hierarchy of exceptions used throughout PaperGen
to provide clear, actionable error messages and enable proper error handling.
"""

from typing import Optional


class PaperGenException(Exception):
    """Base exception for all PaperGen errors.

    All custom exceptions in PaperGen inherit from this class,
    making it easy to catch all PaperGen-specific errors.
    """
    pass


# Project-related exceptions
class ProjectError(PaperGenException):
    """Base class for project-related errors."""
    pass


class ProjectNotFoundError(ProjectError):
    """Raised when a PaperGen project directory is not found.

    This typically occurs when running commands outside a project directory
    or when the .papergen directory is missing.
    """
    def __init__(self, path: str):
        self.path = path
        super().__init__(f"No PaperGen project found at: {path}")


class ProjectAlreadyExistsError(ProjectError):
    """Raised when trying to initialize a project in a directory that already has one."""
    def __init__(self, path: str):
        self.path = path
        super().__init__(f"PaperGen project already exists at: {path}")


class ProjectStateError(ProjectError):
    """Raised when project state is invalid or corrupted."""
    def __init__(self, message: str):
        super().__init__(f"Project state error: {message}")


# API-related exceptions
class APIError(PaperGenException):
    """Base class for API-related errors."""
    pass


class APIConnectionError(APIError):
    """Raised when unable to connect to an API."""
    def __init__(self, provider: str, message: str):
        self.provider = provider
        super().__init__(f"Failed to connect to {provider} API: {message}")


class APIAuthenticationError(APIError):
    """Raised when API authentication fails."""
    def __init__(self, provider: str):
        self.provider = provider
        super().__init__(
            f"Authentication failed for {provider} API. "
            f"Please check your API key in config or environment variables."
        )


class APIRateLimitError(APIError):
    """Raised when API rate limit is exceeded."""
    def __init__(self, provider: str, retry_after: Optional[int] = None):
        self.provider = provider
        self.retry_after = retry_after
        message = f"Rate limit exceeded for {provider} API."
        if retry_after:
            message += f" Retry after {retry_after} seconds."
        super().__init__(message)


class APIResponseError(APIError):
    """Raised when API returns an error response."""
    def __init__(self, provider: str, status_code: int, message: str):
        self.provider = provider
        self.status_code = status_code
        self.message = message
        super().__init__(
            f"{provider} API error (status {status_code}): {message}"
        )


class APITimeoutError(APIError):
    """Raised when API request times out."""
    def __init__(self, provider: str, timeout: int):
        self.provider = provider
        self.timeout = timeout
        super().__init__(
            f"{provider} API request timed out after {timeout} seconds."
        )


# Content extraction exceptions
class ExtractionError(PaperGenException):
    """Base class for content extraction errors."""
    pass


class PDFExtractionError(ExtractionError):
    """Raised when PDF extraction fails."""
    def __init__(self, file_path: str, reason: str):
        self.file_path = file_path
        self.reason = reason
        super().__init__(f"Failed to extract PDF '{file_path}': {reason}")


class WebExtractionError(ExtractionError):
    """Raised when web content extraction fails."""
    def __init__(self, url: str, reason: str):
        self.url = url
        self.reason = reason
        super().__init__(f"Failed to extract content from '{url}': {reason}")


class EmptyContentError(ExtractionError):
    """Raised when extracted content is empty or too short."""
    def __init__(self, source: str, min_length: int = 100):
        self.source = source
        self.min_length = min_length
        super().__init__(
            f"Extracted content from '{source}' is empty or too short "
            f"(minimum {min_length} characters required)."
        )


# Configuration exceptions
class ConfigurationError(PaperGenException):
    """Base class for configuration errors."""
    pass


class InvalidConfigError(ConfigurationError):
    """Raised when configuration is invalid."""
    def __init__(self, field: str, reason: str):
        self.field = field
        self.reason = reason
        super().__init__(f"Invalid configuration for '{field}': {reason}")


class MissingConfigError(ConfigurationError):
    """Raised when required configuration is missing."""
    def __init__(self, field: str):
        self.field = field
        super().__init__(
            f"Missing required configuration: '{field}'. "
            f"Please set it in config file or environment variables."
        )


class APIKeyNotFoundError(ConfigurationError):
    """Raised when API key is not found."""
    def __init__(self, provider: str):
        self.provider = provider
        super().__init__(
            f"API key for {provider} not found. "
            f"Please set it in config file or environment variable."
        )


# Source management exceptions
class SourceError(PaperGenException):
    """Base class for source management errors."""
    pass


class SourceNotFoundError(SourceError):
    """Raised when a source is not found."""
    def __init__(self, source_id: str):
        self.source_id = source_id
        super().__init__(f"Source not found: {source_id}")


class DuplicateSourceError(SourceError):
    """Raised when trying to add a duplicate source."""
    def __init__(self, source_id: str):
        self.source_id = source_id
        super().__init__(f"Source already exists: {source_id}")


# Document generation exceptions
class DocumentError(PaperGenException):
    """Base class for document generation errors."""
    pass


class OutlineError(DocumentError):
    """Raised when outline generation or validation fails."""
    def __init__(self, message: str):
        super().__init__(f"Outline error: {message}")


class DraftError(DocumentError):
    """Raised when draft generation fails."""
    def __init__(self, section_id: str, reason: str):
        self.section_id = section_id
        self.reason = reason
        super().__init__(f"Failed to draft section '{section_id}': {reason}")


class RevisionError(DocumentError):
    """Raised when revision fails."""
    def __init__(self, section_id: str, reason: str):
        self.section_id = section_id
        self.reason = reason
        super().__init__(f"Failed to revise section '{section_id}': {reason}")


class FormattingError(DocumentError):
    """Raised when document formatting fails."""
    def __init__(self, format_type: str, reason: str):
        self.format_type = format_type
        self.reason = reason
        super().__init__(f"Failed to format as {format_type}: {reason}")


# Citation exceptions
class CitationError(PaperGenException):
    """Base class for citation-related errors."""
    pass


class InvalidCitationError(CitationError):
    """Raised when citation format is invalid."""
    def __init__(self, citation: str, reason: str):
        self.citation = citation
        self.reason = reason
        super().__init__(f"Invalid citation '{citation}': {reason}")


class CitationNotFoundError(CitationError):
    """Raised when a citation is not found."""
    def __init__(self, citation_key: str):
        self.citation_key = citation_key
        super().__init__(f"Citation not found: {citation_key}")


# Validation exceptions
class ValidationError(PaperGenException):
    """Base class for validation errors."""
    pass


class InvalidInputError(ValidationError):
    """Raised when user input is invalid."""
    def __init__(self, field: str, value: str, reason: str):
        self.field = field
        self.value = value
        self.reason = reason
        super().__init__(f"Invalid {field} '{value}': {reason}")


class FileValidationError(ValidationError):
    """Raised when file validation fails."""
    def __init__(self, file_path: str, reason: str):
        self.file_path = file_path
        self.reason = reason
        super().__init__(f"File validation failed for '{file_path}': {reason}")


# Research discovery exceptions
class DiscoveryError(PaperGenException):
    """Base class for research discovery errors."""
    pass


class PaperSearchError(DiscoveryError):
    """Raised when paper search fails."""
    def __init__(self, query: str, reason: str):
        self.query = query
        self.reason = reason
        super().__init__(f"Paper search failed for '{query}': {reason}")


class PaperNotFoundError(DiscoveryError):
    """Raised when a paper is not found."""
    def __init__(self, paper_id: str):
        self.paper_id = paper_id
        super().__init__(f"Paper not found: {paper_id}")


# Helper function for exception mapping
def map_http_status_to_exception(status_code: int, provider: str, message: str) -> APIError:
    """Map HTTP status codes to appropriate exceptions.

    Args:
        status_code: HTTP status code
        provider: API provider name
        message: Error message

    Returns:
        Appropriate APIError subclass
    """
    if status_code == 401 or status_code == 403:
        return APIAuthenticationError(provider)
    elif status_code == 429:
        return APIRateLimitError(provider)
    elif status_code >= 500:
        return APIConnectionError(provider, f"Server error: {message}")
    else:
        return APIResponseError(provider, status_code, message)
