"""Research organization using AI (will be completed in Phase 3)."""

from pathlib import Path
from typing import List, Dict, Any


class ResearchOrganizer:
    """Organizes extracted research using AI."""

    def __init__(self, claude_client=None):
        """Initialize organizer with Claude client (to be implemented)."""
        self.claude_client = claude_client

    def organize(
        self,
        sources: List[Dict[str, Any]],
        focus: str = "",
        topic: str = ""
    ) -> str:
        """
        Organize research sources into coherent notes.

        Args:
            sources: List of extracted source dictionaries
            focus: Optional focus areas for organization
            topic: Research topic

        Returns:
            Organized research as markdown text
        """
        if not self.claude_client:
            # Fallback to basic organization if no Claude client
            return self._basic_organization(sources, focus)

        # AI-powered organization using Claude
        from ..ai.prompts import PromptLibrary

        # Prepare source texts
        source_texts = []
        for source in sources:
            metadata = source.get('metadata', {})
            content = source.get('content', {})

            text_parts = []
            text_parts.append(f"Title: {metadata.get('title', 'Untitled')}")

            if metadata.get('authors'):
                authors = metadata['authors']
                if isinstance(authors, list):
                    text_parts.append(f"Authors: {', '.join(authors)}")

            abstract = content.get('abstract') or metadata.get('abstract')
            if abstract:
                text_parts.append(f"Abstract: {abstract}")

            keywords = content.get('keywords', [])
            if keywords:
                text_parts.append(f"Keywords: {', '.join(keywords)}")

            # Add main content (limited)
            full_text = content.get('full_text', '')
            if full_text:
                preview = full_text[:3000]  # More content for AI
                text_parts.append(f"Content: {preview}")

            source_texts.append("\n".join(text_parts))

        # Generate organization prompt
        system_prompt, user_prompt = PromptLibrary.research_organization(
            source_texts,
            focus,
            topic
        )

        try:
            # Use Claude to organize
            organized = self.claude_client.generate(
                prompt=user_prompt,
                system=system_prompt,
                max_tokens=8000,
                temperature=0.7
            )
            return organized

        except Exception as e:
            # Fallback to basic organization on error
            return self._basic_organization(sources, focus) + f"\n\n---\n\nNote: AI organization failed ({str(e)}), using basic organization."

    def _basic_organization(self, sources: List[Dict[str, Any]], focus: str) -> str:
        """Basic organization without AI (temporary)."""
        organized = []

        organized.append("# Organized Research\n")
        if focus:
            organized.append(f"**Focus:** {focus}\n")

        organized.append(f"\n## Sources ({len(sources)} total)\n")

        for i, source in enumerate(sources, 1):
            metadata = source.get('metadata', {})
            content = source.get('content', {})

            organized.append(f"\n### {i}. {metadata.get('title', 'Untitled')}")

            if metadata.get('authors'):
                authors = metadata['authors']
                if isinstance(authors, list):
                    organized.append(f"\n**Authors:** {', '.join(authors)}")
                else:
                    organized.append(f"\n**Authors:** {authors}")

            # Add abstract if available
            abstract = content.get('abstract') or metadata.get('abstract')
            if abstract:
                organized.append(f"\n\n**Abstract:** {abstract}")

            # Add keywords if available
            keywords = content.get('keywords', [])
            if keywords:
                organized.append(f"\n\n**Keywords:** {', '.join(keywords)}")

            # Add brief summary of content
            full_text = content.get('full_text', '')
            if full_text:
                preview = full_text[:500] + "..." if len(full_text) > 500 else full_text
                organized.append(f"\n\n**Content Preview:**\n{preview}")

            organized.append("\n\n---\n")

        return '\n'.join(organized)

    def identify_themes(self, sources: List[Dict]) -> List[str]:
        """Identify common themes across sources (placeholder)."""
        # Will be implemented with AI in Phase 3
        return ["Theme identification requires AI integration (Phase 3)"]

    def extract_methodologies(self, sources: List[Dict]) -> List[str]:
        """Extract methodologies from sources (placeholder)."""
        # Will be implemented with AI in Phase 3
        return ["Methodology extraction requires AI integration (Phase 3)"]

    def find_gaps(self, sources: List[Dict]) -> List[str]:
        """Identify research gaps (placeholder)."""
        # Will be implemented with AI in Phase 3
        return ["Gap analysis requires AI integration (Phase 3)"]
