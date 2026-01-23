"""Pytest configuration and fixtures for PaperGen tests."""

import pytest
from pathlib import Path
import tempfile
import shutil
from datetime import datetime
import json

from papergen.core.project import PaperProject
from papergen.core.state import ProjectState, ProjectMetadata
from papergen.core.config import Config


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # Cleanup
    if temp_path.exists():
        shutil.rmtree(temp_path)


@pytest.fixture
def sample_project(temp_dir):
    """Create a sample PaperGen project."""
    project = PaperProject(temp_dir)
    state = project.initialize(
        topic="Test Paper on Machine Learning",
        template="ieee",
        format="latex",
        metadata={
            "title": "Test Paper",
            "authors": ["Test Author"],
            "abstract": "This is a test abstract"
        }
    )
    return project


@pytest.fixture
def sample_pdf_path():
    """Path to a sample PDF file."""
    # This would point to a real test PDF in fixtures
    return Path(__file__).parent / "fixtures" / "sample_paper.pdf"


@pytest.fixture
def sample_text_content():
    """Sample text content for testing."""
    return """
    Abstract

    This is a sample research paper abstract. It contains enough text to pass
    validation checks and demonstrates the structure of a typical academic paper.

    Introduction

    Machine learning has revolutionized many fields of computer science. This paper
    explores novel approaches to deep learning architectures. We present a new
    method that improves upon existing techniques.

    Related Work

    Previous work in this area includes Smith et al. (2020) and Jones (2021).
    These studies laid the foundation for our approach.

    Methods

    Our methodology consists of three main steps: data preprocessing, model
    training, and evaluation. We use a dataset of 10,000 samples.

    Results

    Our experiments show a 15% improvement over baseline methods. The results
    are statistically significant (p < 0.05).

    Conclusion

    We have presented a novel approach to machine learning that demonstrates
    significant improvements. Future work will explore additional applications.

    References

    Smith, J. et al. (2020). Deep Learning Advances. Journal of AI, 15(3), 234-256.
    Jones, A. (2021). Neural Network Architectures. Proceedings of ICML.
    """


@pytest.fixture
def sample_extracted_content():
    """Sample extracted content structure."""
    return {
        "metadata": {
            "title": "Sample Paper",
            "authors": ["Author One", "Author Two"],
            "year": 2023
        },
        "content": {
            "full_text": "This is the full text of the paper...",
            "sections": [
                {"title": "Abstract", "content": "Abstract content..."},
                {"title": "Introduction", "content": "Introduction content..."},
                {"title": "Methods", "content": "Methods content..."},
                {"title": "Results", "content": "Results content..."},
                {"title": "Conclusion", "content": "Conclusion content..."}
            ],
            "abstract": "Abstract content...",
            "keywords": ["machine learning", "deep learning", "neural networks"]
        },
        "citations": [
            "Smith et al. (2020)",
            "Jones (2021)"
        ],
        "figures": [],
        "tables": []
    }


@pytest.fixture
def mock_claude_response():
    """Mock response from Claude API."""
    return """
    {
        "outline": {
            "sections": [
                {
                    "id": "abstract",
                    "title": "Abstract",
                    "description": "Brief summary of the paper"
                },
                {
                    "id": "introduction",
                    "title": "Introduction",
                    "description": "Background and motivation"
                },
                {
                    "id": "methods",
                    "title": "Methods",
                    "description": "Research methodology"
                }
            ]
        }
    }
    """


@pytest.fixture
def mock_api_key(monkeypatch):
    """Mock API key for testing."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key-12345")
    return "test-api-key-12345"


@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return {
        "api": {
            "provider": "anthropic",
            "model": "claude-sonnet-4-5-20250929",
            "temperature": 0.7,
            "max_tokens": 4096
        },
        "paper": {
            "template": "ieee",
            "format": "latex",
            "citation_style": "apa"
        },
        "word_counts": {
            "abstract": 250,
            "introduction": 1500,
            "methods": 1500,
            "results": 1500,
            "conclusion": 500
        }
    }


@pytest.fixture
def sample_project_state():
    """Sample project state for testing."""
    return ProjectState(
        project_id="test-project-123",
        topic="Machine Learning Research",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        template="ieee",
        format="latex",
        metadata=ProjectMetadata(
            title="Test Paper",
            authors=["Test Author"],
            abstract="Test abstract"
        )
    )


@pytest.fixture
def sample_sources():
    """Sample research sources."""
    return [
        {
            "id": "source_001",
            "type": "pdf",
            "title": "Deep Learning Fundamentals",
            "authors": ["Smith, J.", "Doe, A."],
            "year": 2020,
            "path": "sources/pdfs/paper1.pdf"
        },
        {
            "id": "source_002",
            "type": "web",
            "title": "Neural Network Architectures",
            "url": "https://example.com/paper2",
            "year": 2021
        }
    ]


@pytest.fixture
def sample_outline():
    """Sample paper outline."""
    return {
        "sections": [
            {
                "id": "abstract",
                "title": "Abstract",
                "description": "Summary of the paper",
                "word_count": 250
            },
            {
                "id": "introduction",
                "title": "Introduction",
                "description": "Background and motivation",
                "word_count": 1500,
                "subsections": [
                    {"id": "intro_background", "title": "Background"},
                    {"id": "intro_motivation", "title": "Motivation"}
                ]
            },
            {
                "id": "methods",
                "title": "Methods",
                "description": "Research methodology",
                "word_count": 1500
            },
            {
                "id": "results",
                "title": "Results",
                "description": "Experimental results",
                "word_count": 1500
            },
            {
                "id": "conclusion",
                "title": "Conclusion",
                "description": "Summary and future work",
                "word_count": 500
            }
        ]
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "requires_api: mark test as requiring API access"
    )
