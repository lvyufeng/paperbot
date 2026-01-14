"""Context management for optimizing Claude's token window."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ContextComponent:
    """A component to include in context."""
    content: str
    priority: int = 5  # 1-10, higher is more important
    token_estimate: int = 0
    label: str = ""


class ContextManager:
    """Manages Claude's context window efficiently."""

    def __init__(self, max_tokens: int = 180000):
        """
        Initialize context manager.

        Args:
            max_tokens: Maximum tokens for context (leave room for response)
        """
        self.max_tokens = max_tokens

    def build_context(
        self,
        components: List[ContextComponent],
        required_components: Optional[List[str]] = None
    ) -> str:
        """
        Build optimized context from components.

        Args:
            components: List of context components
            required_components: Labels of components that must be included

        Returns:
            Optimized context string
        """
        # Estimate tokens for all components
        for component in components:
            if component.token_estimate == 0:
                component.token_estimate = self._estimate_tokens(component.content)

        # Separate required and optional components
        required = []
        optional = []

        for component in components:
            if required_components and component.label in required_components:
                required.append(component)
            else:
                optional.append(component)

        # Sort optional by priority (highest first)
        optional.sort(key=lambda x: x.priority, reverse=True)

        # Build context starting with required
        context_parts = []
        total_tokens = 0

        # Add required components
        for component in required:
            if total_tokens + component.token_estimate > self.max_tokens:
                # Truncate if necessary
                remaining_tokens = self.max_tokens - total_tokens
                truncated = self._truncate_to_tokens(component.content, remaining_tokens)
                context_parts.append(truncated)
                break
            else:
                context_parts.append(component.content)
                total_tokens += component.token_estimate

        # Add optional components by priority
        for component in optional:
            if total_tokens + component.token_estimate > self.max_tokens:
                # Try to fit a truncated version
                remaining_tokens = self.max_tokens - total_tokens
                if remaining_tokens > 1000:  # Only if we have meaningful space
                    truncated = self._truncate_to_tokens(component.content, remaining_tokens)
                    context_parts.append(truncated)
                break
            else:
                context_parts.append(component.content)
                total_tokens += component.token_estimate

        return "\n\n---\n\n".join(context_parts)

    def prioritize_sources(
        self,
        sources: List[Dict[str, Any]],
        query: str = "",
        max_sources: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Prioritize sources based on relevance.

        Args:
            sources: List of source dictionaries
            query: Query or topic to match against
            max_sources: Maximum number of sources to return

        Returns:
            Prioritized list of sources
        """
        # Simple prioritization based on keyword matching
        if not query:
            return sources[:max_sources]

        query_terms = set(query.lower().split())

        # Score each source
        scored_sources = []
        for source in sources:
            score = 0

            # Check title
            title = source.get('metadata', {}).get('title', '')
            if title:
                title_terms = set(title.lower().split())
                score += len(query_terms & title_terms) * 3

            # Check abstract
            abstract = source.get('content', {}).get('abstract', '')
            if abstract:
                abstract_terms = set(abstract.lower().split())
                score += len(query_terms & abstract_terms) * 2

            # Check keywords
            keywords = source.get('content', {}).get('keywords', [])
            for keyword in keywords:
                if any(term in keyword.lower() for term in query_terms):
                    score += 2

            scored_sources.append((score, source))

        # Sort by score and return top sources
        scored_sources.sort(key=lambda x: x[0], reverse=True)
        return [source for score, source in scored_sources[:max_sources]]

    def chunk_large_content(
        self,
        content: str,
        chunk_size: int = 50000
    ) -> List[str]:
        """
        Chunk large content into manageable pieces.

        Args:
            content: Content to chunk
            chunk_size: Target token size per chunk

        Returns:
            List of content chunks
        """
        # Convert token size to character size (rough approximation)
        char_size = chunk_size * 4

        if len(content) <= char_size:
            return [content]

        chunks = []
        start = 0

        while start < len(content):
            end = start + char_size

            # Try to break at paragraph boundary
            if end < len(content):
                # Look for paragraph break
                paragraph_break = content.rfind('\n\n', start, end)
                if paragraph_break > start:
                    end = paragraph_break

            chunks.append(content[start:end].strip())
            start = end

        return chunks

    def summarize_for_context(
        self,
        content: str,
        max_length: int = 2000
    ) -> str:
        """
        Create a summary for context (placeholder for now).

        Args:
            content: Content to summarize
            max_length: Maximum length of summary

        Returns:
            Summarized content
        """
        # Simple truncation for now
        # In a full implementation, this could use Claude to generate summaries
        if len(content) <= max_length:
            return content

        # Take beginning and end
        half = max_length // 2
        return f"{content[:half]}\n\n[... content truncated ...]\n\n{content[-half:]}"

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        # Simple estimation: ~4 characters per token
        return len(text) // 4

    def _truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """Truncate text to approximately max_tokens."""
        max_chars = max_tokens * 4
        if len(text) <= max_chars:
            return text

        return text[:max_chars] + "\n\n[... truncated ...]"
