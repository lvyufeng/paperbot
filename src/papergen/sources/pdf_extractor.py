"""PDF extraction for research papers."""

from pathlib import Path
from typing import Dict, List, Any, Optional
import json
import re

import pdfplumber
from PyPDF2 import PdfReader

from ..core.state import Source, SourceType


class PDFExtractor:
    """Extract content from PDF research papers."""

    def __init__(self):
        self.extract_figures = True
        self.extract_tables = True

    def extract(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Extract content from PDF file.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dictionary with extracted content
        """
        content = {
            "full_text": "",
            "sections": [],
            "abstract": None,
            "keywords": [],
        }

        metadata = self._extract_metadata(pdf_path)
        text = self._extract_text(pdf_path)
        content["full_text"] = text

        # Try to identify sections
        sections = self._parse_sections(text)
        content["sections"] = sections

        # Try to extract abstract
        abstract = self._extract_abstract(text)
        if abstract:
            content["abstract"] = abstract

        # Try to extract keywords
        keywords = self._extract_keywords(text)
        if keywords:
            content["keywords"] = keywords

        # Extract citations
        citations = self._extract_citations(text)

        # Extract figures (if enabled)
        figures = []
        if self.extract_figures:
            figures = self._extract_figures(pdf_path)

        # Extract tables (if enabled)
        tables = []
        if self.extract_tables:
            tables = self._extract_tables(pdf_path)

        return {
            "metadata": metadata,
            "content": content,
            "citations": citations,
            "figures": figures,
            "tables": tables,
        }

    def _extract_metadata(self, pdf_path: Path) -> Dict[str, Any]:
        """Extract PDF metadata."""
        try:
            reader = PdfReader(str(pdf_path))
            info = reader.metadata or {}

            metadata = {
                "filename": pdf_path.name,
                "pages": len(reader.pages),
                "title": info.get("/Title", ""),
                "author": info.get("/Author", ""),
                "subject": info.get("/Subject", ""),
                "creator": info.get("/Creator", ""),
            }

            # Parse author field if it exists
            if metadata["author"]:
                # Simple parsing - split by common delimiters
                authors = re.split(r'[,;]|\sand\s', metadata["author"])
                metadata["authors"] = [a.strip() for a in authors if a.strip()]
            else:
                metadata["authors"] = []

            return metadata
        except Exception as e:
            return {
                "filename": pdf_path.name,
                "pages": 0,
                "error": str(e),
                "authors": [],
            }

    def _extract_text(self, pdf_path: Path) -> str:
        """Extract all text from PDF."""
        try:
            text_parts = []
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)

            return "\n\n".join(text_parts)
        except Exception as e:
            # Fallback to PyPDF2
            try:
                reader = PdfReader(str(pdf_path))
                text_parts = []
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                return "\n\n".join(text_parts)
            except Exception:
                return f"Error extracting text: {str(e)}"

    def _parse_sections(self, text: str) -> List[Dict[str, Any]]:
        """Parse document sections based on common headings."""
        sections = []

        # Common academic section patterns (case insensitive)
        section_patterns = [
            r'\n\s*(Abstract|ABSTRACT)\s*\n',
            r'\n\s*(\d+\.?\s+Introduction|INTRODUCTION)\s*\n',
            r'\n\s*(\d+\.?\s+Background|BACKGROUND)\s*\n',
            r'\n\s*(\d+\.?\s+Related\s+Work|RELATED\s+WORK)\s*\n',
            r'\n\s*(\d+\.?\s+Literature\s+Review|LITERATURE\s+REVIEW)\s*\n',
            r'\n\s*(\d+\.?\s+Methodology|METHODOLOGY|Methods|METHODS)\s*\n',
            r'\n\s*(\d+\.?\s+Results|RESULTS)\s*\n',
            r'\n\s*(\d+\.?\s+Discussion|DISCUSSION)\s*\n',
            r'\n\s*(\d+\.?\s+Conclusion|CONCLUSION)\s*\n',
            r'\n\s*(\d+\.?\s+References|REFERENCES)\s*\n',
        ]

        # Find all section markers
        markers = []
        for pattern in section_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                markers.append((match.start(), match.end(), match.group(1).strip()))

        # Sort by position
        markers.sort(key=lambda x: x[0])

        # Extract section content
        for i, (start, end, title) in enumerate(markers):
            # Get text until next section or end
            if i < len(markers) - 1:
                content_end = markers[i + 1][0]
            else:
                content_end = len(text)

            section_text = text[end:content_end].strip()

            sections.append({
                "title": title,
                "text": section_text[:5000],  # Limit section length
                "position": start,
            })

        return sections

    def _extract_abstract(self, text: str) -> Optional[str]:
        """Extract abstract from paper."""
        # Look for abstract section
        pattern = r'\babstract\b\s*[:\-]?\s*(.*?)(?:\n\s*\n|\n\s*(?:introduction|keywords|1\.|I\.))'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)

        if match:
            abstract = match.group(1).strip()
            # Limit length
            if len(abstract) > 2000:
                abstract = abstract[:2000] + "..."
            return abstract

        return None

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from paper."""
        # Look for keywords section
        pattern = r'\b(?:keywords?|key\s+words?)\b\s*[:\-]?\s*(.*?)(?:\n\s*\n|\n\s*(?:introduction|abstract|1\.))'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)

        if match:
            keywords_text = match.group(1).strip()
            # Split by common delimiters
            keywords = re.split(r'[,;·•]', keywords_text)
            keywords = [k.strip() for k in keywords if k.strip()]
            # Limit to first 10
            return keywords[:10]

        return []

    def _extract_citations(self, text: str) -> List[Dict[str, str]]:
        """Extract citation patterns from text."""
        citations = []

        # Pattern 1: Author et al., year
        pattern1 = r'\b([A-Z][a-z]+(?:\s+et\s+al\.?)?),?\s+(\d{4})\b'
        matches1 = re.finditer(pattern1, text)

        for match in matches1:
            # Get context around citation
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end].strip()

            citations.append({
                "text": match.group(0),
                "author": match.group(1),
                "year": match.group(2),
                "context": context,
            })

        # Limit to 100 citations
        return citations[:100]

    def _extract_figures(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """Extract figure information (placeholder - simplified)."""
        figures = []

        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    # Look for figure captions in text
                    text = page.extract_text() or ""
                    fig_pattern = r'(Figure|Fig\.?)\s+(\d+)[:\.]?\s+([^\n]+)'

                    for match in re.finditer(fig_pattern, text, re.IGNORECASE):
                        figures.append({
                            "id": f"fig_{match.group(2)}",
                            "number": match.group(2),
                            "caption": match.group(3).strip()[:200],
                            "page": page_num + 1,
                        })
        except Exception:
            pass

        return figures

    def _extract_tables(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """Extract table information."""
        tables = []

        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    # Extract tables using pdfplumber
                    page_tables = page.extract_tables()

                    for table_num, table_data in enumerate(page_tables):
                        if table_data and len(table_data) > 0:
                            # Look for table caption in text
                            text = page.extract_text() or ""
                            caption_pattern = r'(Table)\s+(\d+)[:\.]?\s+([^\n]+)'
                            caption_match = re.search(caption_pattern, text, re.IGNORECASE)

                            caption = ""
                            if caption_match:
                                caption = caption_match.group(3).strip()[:200]

                            tables.append({
                                "id": f"table_{page_num}_{table_num}",
                                "caption": caption,
                                "page": page_num + 1,
                                "rows": len(table_data),
                                "cols": len(table_data[0]) if table_data else 0,
                            })
        except Exception:
            pass

        return tables
