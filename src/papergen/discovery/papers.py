"""Paper finder module for identifying critical papers."""

from typing import Dict, List, Any, Optional
from pathlib import Path
import json

from ..ai.claude_client import ClaudeClient
from ..core.logging_config import get_logger


class PaperFinder:
    """Identifies and analyzes critical papers in a research area."""

    def __init__(self):
        """Initialize paper finder."""
        self.logger = get_logger()
        self.client = ClaudeClient()
        self.papers: List[Dict[str, Any]] = []
        self.deep_analyses: Dict[str, Dict[str, Any]] = {}

    def analyze_paper(self, content: str, title: str) -> Dict[str, Any]:
        """
        Deep analysis of a single paper.

        Args:
            content: Paper content (extracted text)
            title: Paper title

        Returns:
            Deep analysis results
        """
        self.logger.info(f"Deep analyzing paper: {title}")

        prompt = self._build_deep_analysis_prompt(content, title)
        system = self._get_deep_analysis_system()

        response = self.client.generate(
            prompt=prompt,
            system=system,
            max_tokens=6000,
            temperature=0.3
        )

        analysis = self._parse_response(response)
        self.deep_analyses[title] = analysis
        return analysis

    def _get_deep_analysis_system(self) -> str:
        """Get system prompt for deep paper analysis."""
        return """You are an expert research advisor helping a postgraduate student deeply understand a research paper.

Analyze the paper to extract:
1. Core contribution and novelty
2. Methodology details
3. Experimental setup and results
4. Strengths and weaknesses
5. How this paper can inspire new research

Be critical, thorough, and focus on insights useful for a student wanting to build upon this work."""

    def _build_deep_analysis_prompt(self, content: str, title: str) -> str:
        """Build prompt for deep paper analysis."""
        return f"""Deeply analyze this paper: "{title}"

Paper Content:
{content[:40000]}

Provide analysis in JSON format:
{{
    "title": "{title}",
    "core_contribution": "What is the main novelty?",
    "problem_addressed": "What problem does it solve?",
    "methodology": {{
        "approach": "High-level approach",
        "key_techniques": ["technique1", "technique2"],
        "innovations": ["what's new in the method"]
    }},
    "experiments": {{
        "datasets": ["dataset1"],
        "baselines": ["baseline1"],
        "main_results": "Summary of results",
        "ablation_insights": "What ablations reveal"
    }},
    "strengths": ["strength1", "strength2"],
    "weaknesses": ["weakness1", "weakness2"],
    "limitations_acknowledged": ["limitation1"],
    "future_work_suggested": ["direction1"],
    "inspiration_for_new_research": [
        {{"idea": "...", "how_to_extend": "..."}}
    ],
    "key_equations_or_algorithms": ["description of key formulas"],
    "reproducibility_score": "high/medium/low",
    "recommended_follow_up_papers": ["paper1", "paper2"]
}}"""

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response."""
        try:
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
            return {"raw_response": response}
        except json.JSONDecodeError:
            return {"raw_response": response}

    def get_inspirations(self, title: str) -> List[Dict[str, Any]]:
        """Get research inspirations from a paper."""
        if title in self.deep_analyses:
            return self.deep_analyses[title].get("inspiration_for_new_research", [])
        return []

    def get_weaknesses(self, title: str) -> List[str]:
        """Get paper weaknesses (potential improvement areas)."""
        if title in self.deep_analyses:
            return self.deep_analyses[title].get("weaknesses", [])
        return []
