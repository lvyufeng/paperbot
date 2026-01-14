"""Citation management for academic papers."""

from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import re


class Citation:
    """Represents a single citation."""

    def __init__(
        self,
        key: str,
        title: str = "",
        authors: List[str] = None,
        year: str = "",
        journal: str = "",
        doi: str = "",
        url: str = "",
        **kwargs
    ):
        self.key = key
        self.title = title
        self.authors = authors or []
        self.year = year
        self.journal = journal
        self.doi = doi
        self.url = url
        self.extra = kwargs

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "key": self.key,
            "title": self.title,
            "authors": self.authors,
            "year": self.year,
            "journal": self.journal,
            "doi": self.doi,
            "url": self.url,
            **self.extra
        }

    def to_bibtex(self, entry_type: str = "article") -> str:
        """Convert to BibTeX format."""
        lines = [f"@{entry_type}{{{self.key},"]

        if self.title:
            lines.append(f'  title={{{self.title}}},')
        if self.authors:
            author_str = ' and '.join(self.authors)
            lines.append(f'  author={{{author_str}}},')
        if self.year:
            lines.append(f'  year={{{self.year}}},')
        if self.journal:
            lines.append(f'  journal={{{self.journal}}},')
        if self.doi:
            lines.append(f'  doi={{{self.doi}}},')
        if self.url:
            lines.append(f'  url={{{self.url}}},')

        lines.append("}")
        return "\n".join(lines)


class CitationManager:
    """Manages citations and bibliography."""

    def __init__(self, style: str = "apa"):
        """
        Initialize citation manager.

        Args:
            style: Citation style (apa, ieee, acm, etc.)
        """
        self.style = style
        self.citations: Dict[str, Citation] = {}
        self.citation_counter = 1

    def add_citation(
        self,
        title: str = "",
        authors: List[str] = None,
        year: str = "",
        **kwargs
    ) -> str:
        """
        Add a citation and return its key.

        Args:
            title: Paper title
            authors: List of authors
            year: Publication year
            **kwargs: Additional citation fields

        Returns:
            Citation key
        """
        # Generate key from author and year
        key = self._generate_key(authors, year)

        # Create citation
        citation = Citation(
            key=key,
            title=title,
            authors=authors or [],
            year=year,
            **kwargs
        )

        self.citations[key] = citation
        return key

    def add_from_dict(self, data: Dict[str, Any]) -> str:
        """Add citation from dictionary."""
        key = data.get('key') or self._generate_key(
            data.get('authors', []),
            data.get('year', '')
        )

        citation = Citation(**{**data, 'key': key})
        self.citations[key] = citation
        return key

    def get_citation(self, key: str) -> Optional[Citation]:
        """Get citation by key."""
        return self.citations.get(key)

    def format_inline(self, key: str) -> str:
        """
        Format inline citation based on style.

        Args:
            key: Citation key

        Returns:
            Formatted inline citation
        """
        citation = self.citations.get(key)
        if not citation:
            return f"[{key}]"

        if self.style == "apa":
            if citation.authors:
                author = citation.authors[0].split(',')[0] if ',' in citation.authors[0] else citation.authors[0].split()[0]
                if len(citation.authors) > 2:
                    author += " et al."
                elif len(citation.authors) == 2:
                    author2 = citation.authors[1].split(',')[0] if ',' in citation.authors[1] else citation.authors[1].split()[0]
                    author += f" & {author2}"
                return f"({author}, {citation.year})"
            return f"({citation.year})"

        elif self.style == "ieee":
            # Numbered citation
            if key not in self.citations:
                return f"[{key}]"
            # Get citation number (order of addition)
            keys = list(self.citations.keys())
            number = keys.index(key) + 1
            return f"[{number}]"

        else:
            # Default format
            return f"[{key}]"

    def generate_bibliography(self) -> str:
        """
        Generate formatted bibliography.

        Returns:
            Formatted bibliography text
        """
        if not self.citations:
            return ""

        lines = ["# References\n"]

        if self.style == "ieee":
            # Numbered format
            for i, (key, citation) in enumerate(self.citations.items(), 1):
                formatted = self._format_bibliography_entry(citation)
                lines.append(f"[{i}] {formatted}")
        else:
            # Alphabetical format
            sorted_citations = sorted(
                self.citations.values(),
                key=lambda c: (c.authors[0] if c.authors else '', c.year)
            )
            for citation in sorted_citations:
                formatted = self._format_bibliography_entry(citation)
                lines.append(formatted)

        return "\n\n".join(lines)

    def _format_bibliography_entry(self, citation: Citation) -> str:
        """Format a single bibliography entry."""
        if self.style == "apa":
            # APA format
            parts = []

            if citation.authors:
                if len(citation.authors) == 1:
                    parts.append(f"{citation.authors[0]}.")
                elif len(citation.authors) <= 7:
                    authors_str = ", ".join(citation.authors[:-1]) + f", & {citation.authors[-1]}"
                    parts.append(f"{authors_str}.")
                else:
                    authors_str = ", ".join(citation.authors[:6]) + ", ... " + citation.authors[-1]
                    parts.append(f"{authors_str}.")

            if citation.year:
                parts.append(f"({citation.year}).")

            if citation.title:
                parts.append(f"{citation.title}.")

            if citation.journal:
                parts.append(f"*{citation.journal}*.")

            if citation.doi:
                parts.append(f"https://doi.org/{citation.doi}")

            return " ".join(parts)

        elif self.style == "ieee":
            # IEEE format
            parts = []

            if citation.authors:
                if len(citation.authors) == 1:
                    parts.append(f"{citation.authors[0]},")
                else:
                    authors_str = ", ".join(citation.authors[:-1]) + f", and {citation.authors[-1]}"
                    parts.append(f"{authors_str},")

            if citation.title:
                parts.append(f'"{citation.title},"')

            if citation.journal:
                parts.append(f"*{citation.journal}*,")

            if citation.year:
                parts.append(f"{citation.year}.")

            return " ".join(parts)

        else:
            # Generic format
            return f"{', '.join(citation.authors)} ({citation.year}). {citation.title}. {citation.journal}."

    def export_bibtex(self) -> str:
        """
        Export all citations as BibTeX.

        Returns:
            BibTeX formatted string
        """
        entries = []
        for citation in self.citations.values():
            entries.append(citation.to_bibtex())
        return "\n\n".join(entries)

    def save(self, path: Path) -> None:
        """Save citations to JSON file."""
        data = {
            "style": self.style,
            "citations": {key: cit.to_dict() for key, cit in self.citations.items()}
        }
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, path: Path) -> 'CitationManager':
        """Load citations from JSON file."""
        with open(path, 'r') as f:
            data = json.load(f)

        manager = cls(style=data.get('style', 'apa'))
        for key, cit_data in data.get('citations', {}).items():
            manager.add_from_dict(cit_data)

        return manager

    def _generate_key(self, authors: Optional[List[str]], year: str) -> str:
        """Generate citation key from author and year."""
        if authors and len(authors) > 0:
            # Get last name of first author
            first_author = authors[0]
            # Handle "Last, First" format
            if ',' in first_author:
                last_name = first_author.split(',')[0].strip()
            else:
                # Handle "First Last" format
                parts = first_author.strip().split()
                last_name = parts[-1] if parts else "unknown"

            # Clean up name
            last_name = re.sub(r'[^a-zA-Z]', '', last_name).lower()

            return f"{last_name}{year}"
        else:
            return f"ref{year or self.citation_counter}"

    def extract_citations_from_text(self, text: str) -> List[str]:
        """
        Extract citation keys from text (format: [CITE:key]).

        Args:
            text: Text containing citation markers

        Returns:
            List of citation keys found
        """
        pattern = r'\[CITE:([^\]]+)\]'
        matches = re.findall(pattern, text)
        return matches

    def replace_citation_markers(self, text: str) -> str:
        """
        Replace [CITE:key] markers with formatted citations.

        Args:
            text: Text containing citation markers

        Returns:
            Text with formatted citations
        """
        def replace_match(match):
            key = match.group(1)
            return self.format_inline(key)

        pattern = r'\[CITE:([^\]]+)\]'
        return re.sub(pattern, replace_match, text)
