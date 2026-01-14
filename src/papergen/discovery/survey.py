"""Survey analysis module for understanding research landscapes."""

from typing import Dict, List, Any, Optional
from pathlib import Path
import json

from ..ai.claude_client import ClaudeClient
from ..core.config import config
from ..core.logging_config import get_logger


class SurveyAnalyzer:
    """Analyzes survey papers to understand research landscapes."""

    def __init__(self):
        """Initialize survey analyzer."""
        self.logger = get_logger()
        self.client = ClaudeClient()
        self.analysis_results: Dict[str, Any] = {}

    def analyze_survey(self, content: str, topic: str) -> Dict[str, Any]:
        """
        Analyze a survey paper to extract research landscape.

        Args:
            content: Survey paper content (extracted text)
            topic: Research topic/direction

        Returns:
            Analysis results with themes, methods, gaps, etc.
        """
        self.logger.info(f"Analyzing survey for topic: {topic}")

        prompt = self._build_analysis_prompt(content, topic)
        system_prompt = self._get_system_prompt()

        response = self.client.generate(
            prompt=prompt,
            system=system_prompt,
            max_tokens=8000,
            temperature=0.3
        )

        analysis = self._parse_analysis(response)
        self.analysis_results = analysis
        return analysis

    def _get_system_prompt(self) -> str:
        """Get system prompt for survey analysis."""
        return """You are an expert research advisor helping a postgraduate student understand a research field.

Your task is to analyze survey papers and extract:
1. Key research themes and sub-areas
2. Important methods and techniques
3. Benchmark datasets and evaluation metrics
4. Research gaps and open problems
5. Trending directions and future opportunities

Be thorough, academic, and provide actionable insights for a student looking to publish at top-tier AI conferences (ACL, EMNLP, NeurIPS, ICML, AAAI, IJCAI).

Output in structured JSON format."""

    def _build_analysis_prompt(self, content: str, topic: str) -> str:
        """Build prompt for survey analysis."""
        return f"""Analyze this survey paper about "{topic}" and extract the research landscape.

Survey Content:
{content[:50000]}

Please provide a comprehensive analysis in JSON format:
{{
    "topic": "{topic}",
    "research_themes": [
        {{"name": "theme name", "description": "...", "key_papers": ["paper1", "paper2"]}}
    ],
    "methods": [
        {{"name": "method name", "category": "...", "strengths": [...], "limitations": [...]}}
    ],
    "datasets": [
        {{"name": "dataset", "task": "...", "size": "...", "url": "..."}}
    ],
    "metrics": ["metric1", "metric2"],
    "research_gaps": [
        {{"gap": "description", "difficulty": "high/medium/low", "potential_impact": "..."}}
    ],
    "future_directions": [
        {{"direction": "...", "why_promising": "...", "required_resources": "..."}}
    ],
    "key_papers_to_read": [
        {{"title": "...", "why_important": "...", "contribution": "..."}}
    ]
}}"""

    def _parse_analysis(self, response: str) -> Dict[str, Any]:
        """Parse analysis response from AI."""
        try:
            # Extract JSON from response
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
            return {"raw_response": response}
        except json.JSONDecodeError:
            self.logger.warning("Failed to parse JSON, returning raw response")
            return {"raw_response": response}

    def get_research_gaps(self) -> List[Dict[str, Any]]:
        """Get identified research gaps."""
        return self.analysis_results.get("research_gaps", [])

    def get_key_papers(self) -> List[Dict[str, Any]]:
        """Get recommended papers for deep reading."""
        return self.analysis_results.get("key_papers_to_read", [])

    def get_future_directions(self) -> List[Dict[str, Any]]:
        """Get promising future research directions."""
        return self.analysis_results.get("future_directions", [])
