"""Text file extraction for notes and markdown files."""

from pathlib import Path
from typing import Dict, Any


class TextExtractor:
    """Extract content from text/markdown files."""

    def extract(self, text_path: Path) -> Dict[str, Any]:
        """
        Extract content from text file.

        Args:
            text_path: Path to text file

        Returns:
            Dictionary with extracted content
        """
        try:
            with open(text_path, 'r', encoding='utf-8') as f:
                text = f.read()

            metadata = {
                "filename": text_path.name,
                "file_type": text_path.suffix,
            }

            content = {
                "full_text": text,
                "sections": [],
            }

            # Try to parse markdown sections if it's a markdown file
            if text_path.suffix.lower() in ['.md', '.markdown']:
                content["sections"] = self._parse_markdown_sections(text)

            return {
                "metadata": metadata,
                "content": content,
                "citations": [],
                "figures": [],
                "tables": [],
            }
        except Exception as e:
            return {
                "metadata": {
                    "filename": text_path.name,
                    "error": str(e),
                },
                "content": {"full_text": "", "sections": []},
                "citations": [],
                "figures": [],
                "tables": [],
            }

    def _parse_markdown_sections(self, text: str) -> list:
        """Parse sections from markdown headers."""
        sections = []
        lines = text.split('\n')

        current_section = None
        current_content = []

        for line in lines:
            # Check for markdown header
            if line.startswith('#'):
                # Save previous section
                if current_section:
                    sections.append({
                        "title": current_section,
                        "text": '\n'.join(current_content).strip(),
                    })

                # Start new section
                current_section = line.lstrip('#').strip()
                current_content = []
            elif current_section:
                current_content.append(line)

        # Add last section
        if current_section:
            sections.append({
                "title": current_section,
                "text": '\n'.join(current_content).strip(),
            })

        return sections
