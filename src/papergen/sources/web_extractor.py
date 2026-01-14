"""Web content extraction for online sources."""

from pathlib import Path
from typing import Dict, Any, Optional
from urllib.parse import urlparse
import re

import requests
from bs4 import BeautifulSoup


class WebExtractor:
    """Extract content from web sources."""

    def __init__(self):
        self.timeout = 30
        self.user_agent = "PaperGen/1.0"
        self.max_retries = 3

    def extract(self, url: str) -> Dict[str, Any]:
        """
        Extract content from URL.

        Args:
            url: URL to extract from

        Returns:
            Dictionary with extracted content
        """
        # Try to fetch content
        html = self._fetch_url(url)

        if not html:
            return {
                "metadata": {"url": url, "error": "Failed to fetch URL"},
                "content": {"full_text": "", "sections": []},
                "citations": [],
                "figures": [],
                "tables": [],
            }

        # Parse HTML
        soup = BeautifulSoup(html, 'html.parser')

        # Extract metadata
        metadata = self._extract_metadata(soup, url)

        # Extract main content
        content = self._extract_content(soup)

        # Extract citations (if it's an academic page)
        citations = self._extract_citations(content["full_text"])

        return {
            "metadata": metadata,
            "content": content,
            "citations": citations,
            "figures": [],
            "tables": [],
        }

    def _fetch_url(self, url: str) -> Optional[str]:
        """Fetch URL content with retries."""
        headers = {
            "User-Agent": self.user_agent
        }

        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, headers=headers, timeout=self.timeout)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                if attempt == self.max_retries - 1:
                    return None
                continue

        return None

    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract metadata from HTML."""
        metadata = {
            "url": url,
            "title": "",
            "authors": [],
            "source": urlparse(url).netloc,
        }

        # Try to get title
        title_tag = soup.find('title')
        if title_tag:
            metadata["title"] = title_tag.get_text().strip()

        # Try meta tags for better title
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            metadata["title"] = og_title.get('content').strip()

        # Try to get author from meta tags
        author_meta = soup.find('meta', attrs={'name': 'author'})
        if author_meta and author_meta.get('content'):
            authors = author_meta.get('content').strip()
            metadata["authors"] = [a.strip() for a in authors.split(',')]

        # For arXiv, try to get authors from specific structure
        if 'arxiv.org' in url:
            metadata = self._extract_arxiv_metadata(soup, metadata)

        return metadata

    def _extract_arxiv_metadata(self, soup: BeautifulSoup, metadata: Dict) -> Dict:
        """Extract metadata specific to arXiv papers."""
        # Try to get authors from arXiv structure
        authors_div = soup.find('div', class_='authors')
        if authors_div:
            authors = []
            for author_link in authors_div.find_all('a'):
                author_name = author_link.get_text().strip()
                if author_name:
                    authors.append(author_name)
            if authors:
                metadata["authors"] = authors

        # Try to get abstract
        abstract_div = soup.find('blockquote', class_='abstract')
        if abstract_div:
            abstract_text = abstract_div.get_text().strip()
            # Remove "Abstract:" prefix
            abstract_text = re.sub(r'^Abstract:\s*', '', abstract_text, flags=re.IGNORECASE)
            metadata["abstract"] = abstract_text

        return metadata

    def _extract_content(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract main content from HTML."""
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()

        # Try to find main content area
        main_content = None

        # Common content containers
        content_selectors = [
            {'id': 'content'},
            {'id': 'main'},
            {'class': 'content'},
            {'class': 'main-content'},
            {'role': 'main'},
            {'tag': 'main'},
            {'tag': 'article'},
        ]

        for selector in content_selectors:
            if 'id' in selector:
                main_content = soup.find(id=selector['id'])
            elif 'class' in selector:
                main_content = soup.find(class_=selector['class'])
            elif 'role' in selector:
                main_content = soup.find(attrs={'role': selector['role']})
            elif 'tag' in selector:
                main_content = soup.find(selector['tag'])

            if main_content:
                break

        # If no main content found, use body
        if not main_content:
            main_content = soup.find('body')

        if not main_content:
            main_content = soup

        # Extract text
        text = main_content.get_text(separator='\n\n', strip=True)

        # Try to parse sections
        sections = self._parse_sections(main_content)

        return {
            "full_text": text[:50000],  # Limit to 50k chars
            "sections": sections,
        }

    def _parse_sections(self, content_element) -> list:
        """Parse sections from HTML content."""
        sections = []

        # Find all headings
        headings = content_element.find_all(['h1', 'h2', 'h3'])

        for heading in headings[:20]:  # Limit to 20 sections
            title = heading.get_text().strip()
            if not title:
                continue

            # Get content until next heading
            section_content = []
            for sibling in heading.find_next_siblings():
                if sibling.name in ['h1', 'h2', 'h3']:
                    break
                text = sibling.get_text(strip=True)
                if text:
                    section_content.append(text)

            sections.append({
                "title": title,
                "text": "\n\n".join(section_content)[:2000],  # Limit section length
            })

        return sections

    def _extract_citations(self, text: str) -> list:
        """Extract citation patterns from text."""
        citations = []

        # Pattern: Author et al., year
        pattern = r'\b([A-Z][a-z]+(?:\s+et\s+al\.?)?),?\s+(\d{4})\b'
        matches = re.finditer(pattern, text)

        for match in matches:
            # Get context
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end].strip()

            citations.append({
                "text": match.group(0),
                "author": match.group(1),
                "year": match.group(2),
                "context": context,
            })

        return citations[:100]  # Limit to 100
