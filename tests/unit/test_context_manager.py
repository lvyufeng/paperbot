"""Tests for ContextManager."""

import pytest

from papergen.ai.context_manager import ContextManager, ContextComponent


class TestContextComponent:
    """Tests for ContextComponent dataclass."""

    def test_default_values(self):
        """Test default values."""
        component = ContextComponent(content="Test content")

        assert component.content == "Test content"
        assert component.priority == 5
        assert component.token_estimate == 0
        assert component.label == ""

    def test_custom_values(self):
        """Test custom values."""
        component = ContextComponent(
            content="Custom content",
            priority=10,
            token_estimate=500,
            label="important"
        )

        assert component.content == "Custom content"
        assert component.priority == 10
        assert component.token_estimate == 500
        assert component.label == "important"


class TestContextManagerInit:
    """Tests for ContextManager initialization."""

    def test_default_max_tokens(self):
        """Test default max tokens."""
        manager = ContextManager()

        assert manager.max_tokens == 180000

    def test_custom_max_tokens(self):
        """Test custom max tokens."""
        manager = ContextManager(max_tokens=100000)

        assert manager.max_tokens == 100000


class TestContextManagerBuildContext:
    """Tests for build_context method."""

    @pytest.fixture
    def manager(self):
        """Create manager instance."""
        return ContextManager(max_tokens=1000)

    def test_empty_components(self, manager):
        """Test building context from empty list."""
        result = manager.build_context([])

        assert result == ""

    def test_single_component(self, manager):
        """Test building context with single component."""
        components = [ContextComponent(content="Test content")]

        result = manager.build_context(components)

        assert "Test content" in result

    def test_multiple_components(self, manager):
        """Test building context with multiple components."""
        components = [
            ContextComponent(content="Content 1"),
            ContextComponent(content="Content 2"),
            ContextComponent(content="Content 3")
        ]

        result = manager.build_context(components)

        assert "Content 1" in result
        assert "Content 2" in result
        assert "Content 3" in result

    def test_priority_ordering(self, manager):
        """Test that higher priority components are included first."""
        components = [
            ContextComponent(content="Low priority", priority=1),
            ContextComponent(content="High priority", priority=10),
            ContextComponent(content="Medium priority", priority=5)
        ]

        result = manager.build_context(components)

        # All should be included in small context
        assert "High priority" in result
        assert "Medium priority" in result
        assert "Low priority" in result

    def test_required_components(self, manager):
        """Test that required components are always included."""
        components = [
            ContextComponent(content="Required", label="must_have", priority=1),
            ContextComponent(content="Optional", label="optional", priority=10)
        ]

        result = manager.build_context(components, required_components=["must_have"])

        assert "Required" in result

    def test_token_estimation(self, manager):
        """Test that token estimation works."""
        # Create a component without token estimate
        component = ContextComponent(content="Test content")
        assert component.token_estimate == 0

        manager.build_context([component])

        # Token estimate should be set after building
        assert component.token_estimate > 0

    def test_truncation_when_exceeding_max_tokens(self):
        """Test truncation when content exceeds max tokens."""
        # Use a small max_tokens to force truncation
        manager = ContextManager(max_tokens=50)

        # Create a large component
        large_content = "x" * 1000
        components = [ContextComponent(content=large_content)]

        result = manager.build_context(components)

        # Should be truncated - the result should be smaller than original
        assert len(result) < len(large_content)


class TestContextManagerPrioritizeSources:
    """Tests for prioritize_sources method."""

    @pytest.fixture
    def manager(self):
        """Create manager instance."""
        return ContextManager()

    def test_empty_sources(self, manager):
        """Test with empty sources."""
        result = manager.prioritize_sources([])

        assert result == []

    def test_no_query(self, manager):
        """Test without query returns first N sources."""
        sources = [{"id": i} for i in range(20)]

        result = manager.prioritize_sources(sources, max_sources=5)

        assert len(result) == 5
        assert result[0]["id"] == 0

    def test_query_matching_title(self, manager):
        """Test query matching against title."""
        sources = [
            {"metadata": {"title": "Machine Learning Paper"}, "content": {}},
            {"metadata": {"title": "Biology Study"}, "content": {}},
            {"metadata": {"title": "Deep Learning Methods"}, "content": {}}
        ]

        result = manager.prioritize_sources(sources, query="learning", max_sources=10)

        # Learning papers should be ranked higher
        assert len(result) == 3

    def test_query_matching_abstract(self, manager):
        """Test query matching against abstract."""
        sources = [
            {"metadata": {}, "content": {"abstract": "This paper discusses neural networks"}},
            {"metadata": {}, "content": {"abstract": "A study of plants"}},
        ]

        result = manager.prioritize_sources(sources, query="neural", max_sources=10)

        assert len(result) == 2

    def test_query_matching_keywords(self, manager):
        """Test query matching against keywords."""
        sources = [
            {"metadata": {}, "content": {"keywords": ["AI", "machine learning"]}},
            {"metadata": {}, "content": {"keywords": ["biology", "plants"]}},
        ]

        result = manager.prioritize_sources(sources, query="AI", max_sources=10)

        assert len(result) == 2

    def test_max_sources_limit(self, manager):
        """Test max_sources limit."""
        sources = [{"id": i} for i in range(100)]

        result = manager.prioritize_sources(sources, max_sources=5)

        assert len(result) == 5


class TestContextManagerChunkContent:
    """Tests for chunk_large_content method."""

    @pytest.fixture
    def manager(self):
        """Create manager instance."""
        return ContextManager()

    def test_small_content_no_chunking(self, manager):
        """Test small content returns single chunk."""
        content = "Small content"

        result = manager.chunk_large_content(content)

        assert len(result) == 1
        assert result[0] == content

    def test_large_content_chunking(self, manager):
        """Test large content is chunked."""
        # Create content larger than chunk size
        content = "Paragraph 1.\n\n" * 100000

        result = manager.chunk_large_content(content, chunk_size=1000)

        assert len(result) > 1

    def test_respects_paragraph_boundaries(self, manager):
        """Test chunking respects paragraph boundaries."""
        content = "Paragraph one content here.\n\nParagraph two content here.\n\nParagraph three content here."

        result = manager.chunk_large_content(content, chunk_size=10)

        # Should have multiple chunks
        for chunk in result:
            assert chunk.strip() != ""


class TestContextManagerSummarize:
    """Tests for summarize_for_context method."""

    @pytest.fixture
    def manager(self):
        """Create manager instance."""
        return ContextManager()

    def test_short_content_unchanged(self, manager):
        """Test short content is not changed."""
        content = "Short content"

        result = manager.summarize_for_context(content, max_length=1000)

        assert result == content

    def test_long_content_truncated(self, manager):
        """Test long content is truncated."""
        content = "x" * 5000

        result = manager.summarize_for_context(content, max_length=1000)

        assert len(result) <= 1050  # Some overhead for truncation marker
        assert "truncated" in result.lower()

    def test_preserves_beginning_and_end(self, manager):
        """Test that both beginning and end are preserved."""
        content = "START" + "x" * 5000 + "END"

        result = manager.summarize_for_context(content, max_length=1000)

        assert "START" in result
        assert "END" in result


class TestContextManagerPrivateMethods:
    """Tests for private helper methods."""

    @pytest.fixture
    def manager(self):
        """Create manager instance."""
        return ContextManager()

    def test_estimate_tokens(self, manager):
        """Test token estimation."""
        text = "x" * 400

        result = manager._estimate_tokens(text)

        # Approximately 4 chars per token
        assert result == 100

    def test_truncate_to_tokens(self, manager):
        """Test truncation to token limit."""
        text = "x" * 1000

        result = manager._truncate_to_tokens(text, max_tokens=50)

        # 50 tokens * 4 chars = 200 chars
        assert len(result) < 300  # Including truncation message

    def test_truncate_small_text(self, manager):
        """Test truncation doesn't affect small text."""
        text = "small"

        result = manager._truncate_to_tokens(text, max_tokens=1000)

        assert result == text
