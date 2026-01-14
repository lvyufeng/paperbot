"""Outline data structures and management."""

from pathlib import Path
from typing import List, Dict, Any, Optional
import json

from pydantic import BaseModel, Field


class Section(BaseModel):
    """Represents a paper section in the outline."""
    id: str
    title: str
    level: int = 1  # 0=abstract, 1=main section, 2=subsection
    order: int = 0
    objectives: List[str] = Field(default_factory=list)
    key_points: List[str] = Field(default_factory=list)
    word_count_target: int = 1000
    sources: List[str] = Field(default_factory=list)  # Source IDs
    guidance: Optional[str] = None
    subsections: List['Section'] = Field(default_factory=list)

    def to_markdown(self, depth: int = 0) -> str:
        """Convert section to markdown format."""
        indent = "  " * depth
        lines = []

        # Section header
        header_level = "#" * (depth + 1)
        lines.append(f"{header_level} {self.title}")
        lines.append("")

        # Objectives
        if self.objectives:
            lines.append(f"{indent}**Objectives:**")
            for obj in self.objectives:
                lines.append(f"{indent}- {obj}")
            lines.append("")

        # Key points
        if self.key_points:
            lines.append(f"{indent}**Key Points:**")
            for point in self.key_points:
                lines.append(f"{indent}- {point}")
            lines.append("")

        # Target word count
        lines.append(f"{indent}**Target:** {self.word_count_target} words")
        lines.append("")

        # Guidance
        if self.guidance:
            lines.append(f"{indent}**Note:** {self.guidance}")
            lines.append("")

        # Subsections
        if self.subsections:
            for subsection in self.subsections:
                lines.append(subsection.to_markdown(depth + 1))

        return "\n".join(lines)


# Enable forward references
Section.model_rebuild()


class Outline(BaseModel):
    """Represents complete paper outline."""
    version: str = "1.0"
    topic: str
    sections: List[Section] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_json_file(self, path: Path) -> None:
        """Save outline to JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.model_dump(mode='json'), f, indent=2)

    @classmethod
    def from_json_file(cls, path: Path) -> 'Outline':
        """Load outline from JSON file."""
        with open(path, 'r') as f:
            data = json.load(f)
        return cls(**data)

    def to_markdown(self) -> str:
        """Convert entire outline to markdown format."""
        lines = [
            f"# Paper Outline: {self.topic}",
            "",
            f"**Total Sections:** {len(self.sections)}",
            ""
        ]

        # Calculate total word count
        total_words = sum(
            section.word_count_target + sum(sub.word_count_target for sub in section.subsections)
            for section in self.sections
        )
        lines.append(f"**Target Length:** ~{total_words} words")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Add each section
        for section in self.sections:
            lines.append(section.to_markdown())
            lines.append("")

        return "\n".join(lines)

    def get_section_by_id(self, section_id: str) -> Optional[Section]:
        """Get a section by its ID."""
        for section in self.sections:
            if section.id == section_id:
                return section
            # Check subsections
            for subsection in section.subsections:
                if subsection.id == section_id:
                    return subsection
        return None

    def get_all_sections_flat(self) -> List[Section]:
        """Get all sections in a flat list (including subsections)."""
        flat = []
        for section in self.sections:
            flat.append(section)
            flat.extend(section.subsections)
        return flat

    def validate_structure(self) -> bool:
        """Validate that outline structure is valid."""
        # Check for duplicate IDs
        ids = [s.id for s in self.get_all_sections_flat()]
        if len(ids) != len(set(ids)):
            return False

        # Check that all sections have titles
        if any(not s.title for s in self.get_all_sections_flat()):
            return False

        return True


class OutlineGenerator:
    """Generates paper outlines using AI."""

    def __init__(self, claude_client):
        """
        Initialize outline generator.

        Args:
            claude_client: Claude API client
        """
        self.claude_client = claude_client

    def generate(
        self,
        topic: str,
        research_text: str,
        sections: List[str],
        word_count_targets: Optional[Dict[str, int]] = None
    ) -> Outline:
        """
        Generate outline using AI.

        Args:
            topic: Paper topic
            research_text: Organized research text
            sections: List of section names to include
            word_count_targets: Optional word count targets

        Returns:
            Generated Outline object
        """
        from ..ai.prompts import PromptLibrary

        # Generate prompt
        system_prompt, user_prompt = PromptLibrary.outline_generation(
            research_text,
            topic,
            sections,
            word_count_targets
        )

        # Call Claude
        response = self.claude_client.generate(
            prompt=user_prompt,
            system=system_prompt,
            max_tokens=4096,
            temperature=0.7
        )

        # Parse JSON response
        outline_data = self._parse_outline_response(response, topic)

        # Create Outline object
        outline = Outline(
            topic=topic,
            sections=[Section(**section_data) for section_data in outline_data["sections"]],
            metadata={"generated_with": "claude", "sections_requested": sections}
        )

        return outline

    def _parse_outline_response(self, response: str, topic: str) -> Dict:
        """Parse Claude's outline response."""
        import re

        # Try to extract JSON from response
        # Look for JSON code block or raw JSON
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON directly
            json_match = re.search(r'\{.*"sections".*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                # Fallback: create basic outline
                return self._create_fallback_outline(topic)

        try:
            outline_data = json.loads(json_str)
            return outline_data
        except json.JSONDecodeError:
            return self._create_fallback_outline(topic)

    def _create_fallback_outline(self, topic: str) -> Dict:
        """Create a basic fallback outline if parsing fails."""
        return {
            "sections": [
                {
                    "id": "abstract",
                    "title": "Abstract",
                    "level": 0,
                    "order": 0,
                    "objectives": ["Summarize the paper"],
                    "key_points": ["Background", "Methodology", "Results", "Conclusion"],
                    "word_count_target": 250,
                    "sources": [],
                    "subsections": []
                },
                {
                    "id": "introduction",
                    "title": "Introduction",
                    "level": 1,
                    "order": 1,
                    "objectives": ["Introduce the topic", "State the research question"],
                    "key_points": ["Background", "Motivation", "Contributions"],
                    "word_count_target": 1500,
                    "sources": [],
                    "subsections": []
                },
                {
                    "id": "methods",
                    "title": "Methodology",
                    "level": 1,
                    "order": 2,
                    "objectives": ["Describe research methods"],
                    "key_points": ["Approach", "Data", "Analysis"],
                    "word_count_target": 1500,
                    "sources": [],
                    "subsections": []
                },
                {
                    "id": "results",
                    "title": "Results",
                    "level": 1,
                    "order": 3,
                    "objectives": ["Present findings"],
                    "key_points": ["Key findings", "Analysis"],
                    "word_count_target": 1500,
                    "sources": [],
                    "subsections": []
                },
                {
                    "id": "conclusion",
                    "title": "Conclusion",
                    "level": 1,
                    "order": 4,
                    "objectives": ["Summarize contributions", "Future work"],
                    "key_points": ["Summary", "Implications", "Future directions"],
                    "word_count_target": 500,
                    "sources": [],
                    "subsections": []
                }
            ]
        }

    def refine_section(
        self,
        section: Section,
        feedback: str,
        research_text: str
    ) -> Section:
        """
        Refine a section based on feedback.

        Args:
            section: Section to refine
            feedback: User feedback
            research_text: Research context

        Returns:
            Refined Section object
        """
        prompt = f"""Refine the following paper section outline based on user feedback.

Current Section:
- Title: {section.title}
- Objectives: {', '.join(section.objectives)}
- Key Points: {', '.join(section.key_points)}

User Feedback: {feedback}

Research Context (first 2000 chars):
{research_text[:2000]}

Provide an improved version with updated objectives and key points.
Format as JSON:
{{
  "title": "Section Title",
  "objectives": ["obj1", "obj2"],
  "key_points": ["point1", "point2", "point3"],
  "guidance": "any special notes"
}}"""

        response = self.claude_client.generate(
            prompt=prompt,
            max_tokens=1024,
            temperature=0.7
        )

        # Parse response
        import re
        json_match = re.search(r'\{.*?\}', response, re.DOTALL)
        if json_match:
            try:
                refined_data = json.loads(json_match.group(0))
                section.title = refined_data.get('title', section.title)
                section.objectives = refined_data.get('objectives', section.objectives)
                section.key_points = refined_data.get('key_points', section.key_points)
                section.guidance = refined_data.get('guidance', section.guidance)
            except json.JSONDecodeError:
                pass

        return section
