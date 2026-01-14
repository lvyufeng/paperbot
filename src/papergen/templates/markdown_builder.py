"""Markdown document builder."""

from pathlib import Path
from typing import Dict, List, Optional, Any
import re

from ..document.citation import CitationManager


class MarkdownBuilder:
    """Builds Markdown documents from sections."""

    def __init__(self, template: str = "standard"):
        """
        Initialize Markdown builder.

        Args:
            template: Template name (standard, arxiv, github)
        """
        self.template = template
        self.sections_content: Dict[str, str] = {}
        self.metadata: Dict[str, Any] = {}
        self.citation_manager: Optional[CitationManager] = None

    def build(
        self,
        sections: Dict[str, str],
        metadata: Dict[str, Any],
        citation_manager: CitationManager,
        include_toc: bool = True
    ) -> str:
        """
        Build complete Markdown document.

        Args:
            sections: Dictionary of section_id -> content
            metadata: Paper metadata
            citation_manager: Citation manager instance
            include_toc: Include table of contents

        Returns:
            Complete Markdown document as string
        """
        self.sections_content = sections
        self.metadata = metadata
        self.citation_manager = citation_manager

        parts = []

        # Add frontmatter
        parts.append(self._format_frontmatter())
        parts.append("")

        # Add title and metadata
        parts.append(f"# {metadata.get('title', 'Untitled')}")
        parts.append("")

        # Add authors
        authors = metadata.get('authors', [])
        if authors:
            parts.append(f"**Authors:** {', '.join(authors)}")
            parts.append("")

        # Add keywords
        keywords = metadata.get('keywords', [])
        if keywords:
            parts.append(f"**Keywords:** {', '.join(keywords)}")
            parts.append("")

        parts.append("---")
        parts.append("")

        # Add table of contents if requested
        if include_toc:
            parts.append(self._generate_toc())
            parts.append("")

        # Add sections in order
        section_order = ['abstract', 'introduction', 'related_work', 'methods',
                        'methodology', 'results', 'discussion', 'conclusion']

        for section_id in section_order:
            if section_id in sections:
                content = sections[section_id]
                # Replace citation markers with formatted citations
                content = self._format_citations(content)
                parts.append(content)
                parts.append("")

        # Add any remaining sections not in standard order
        for section_id, content in sections.items():
            if section_id not in section_order:
                content = self._format_citations(content)
                parts.append(content)
                parts.append("")

        # Add references
        parts.append(self._format_references())

        return "\n".join(parts)

    def _format_frontmatter(self) -> str:
        """Format YAML frontmatter."""
        if self.template == "arxiv":
            return self._format_arxiv_frontmatter()
        else:
            return self._format_standard_frontmatter()

    def _format_standard_frontmatter(self) -> str:
        """Format standard frontmatter."""
        lines = ["---"]
        lines.append(f"title: \"{self.metadata.get('title', 'Untitled')}\"")

        authors = self.metadata.get('authors', [])
        if authors:
            lines.append("authors:")
            for author in authors:
                lines.append(f"  - {author}")

        keywords = self.metadata.get('keywords', [])
        if keywords:
            lines.append("keywords:")
            for keyword in keywords:
                lines.append(f"  - {keyword}")

        if 'date' in self.metadata:
            lines.append(f"date: {self.metadata['date']}")

        lines.append("---")
        return "\n".join(lines)

    def _format_arxiv_frontmatter(self) -> str:
        """Format arXiv-style frontmatter."""
        lines = ["---"]
        lines.append(f"title: \"{self.metadata.get('title', 'Untitled')}\"")

        authors = self.metadata.get('authors', [])
        if authors:
            lines.append("authors:")
            for author in authors:
                lines.append(f"  - name: {author}")

        if 'abstract' in self.sections_content:
            # Extract abstract text (without header)
            abstract = self.sections_content['abstract']
            abstract_text = re.sub(r'^#+\s*Abstract\s*\n+', '', abstract, flags=re.IGNORECASE)
            lines.append(f"abstract: |")
            for line in abstract_text.split('\n'):
                lines.append(f"  {line}")

        lines.append("---")
        return "\n".join(lines)

    def _generate_toc(self) -> str:
        """Generate table of contents."""
        lines = ["## Table of Contents"]
        lines.append("")

        section_titles = {
            'abstract': 'Abstract',
            'introduction': 'Introduction',
            'related_work': 'Related Work',
            'methods': 'Methods',
            'methodology': 'Methodology',
            'results': 'Results',
            'discussion': 'Discussion',
            'conclusion': 'Conclusion',
        }

        for section_id, content in self.sections_content.items():
            # Try to extract title from content
            title_match = re.search(r'^#+\s*(.+)$', content, re.MULTILINE)
            if title_match:
                title = title_match.group(1)
            else:
                title = section_titles.get(section_id, section_id.replace('_', ' ').title())

            # Create anchor link
            anchor = section_id.replace('_', '-')
            lines.append(f"- [{title}](#{anchor})")

        lines.append("- [References](#references)")

        return "\n".join(lines)

    def _format_citations(self, content: str) -> str:
        """Format citation markers."""
        if not self.citation_manager:
            return content

        return self.citation_manager.replace_citation_markers(content)

    def _format_references(self) -> str:
        """Format references section."""
        if not self.citation_manager or not self.citation_manager.citations:
            return "## References\n\n*No references*"

        return self.citation_manager.generate_bibliography()

    def export_for_platform(self, platform: str) -> str:
        """
        Export formatted for specific platforms.

        Args:
            platform: Platform name (github, arxiv, medium)

        Returns:
            Platform-specific markdown
        """
        # Build standard markdown first
        standard_md = self.build(
            self.sections_content,
            self.metadata,
            self.citation_manager
        )

        if platform == "github":
            # GitHub-flavored markdown (already compatible)
            return standard_md
        elif platform == "arxiv":
            # arXiv format (use arXiv template)
            self.template = "arxiv"
            return self.build(
                self.sections_content,
                self.metadata,
                self.citation_manager,
                include_toc=False
            )
        else:
            return standard_md
