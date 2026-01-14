"""Brainstorm module for generating novel research ideas."""

from typing import Dict, List, Any, Optional
import json

from ..ai.claude_client import ClaudeClient
from ..core.logging_config import get_logger


class IdeaGenerator:
    """Generates and evaluates novel research ideas."""

    def __init__(self):
        """Initialize idea generator."""
        self.logger = get_logger()
        self.client = ClaudeClient()
        self.ideas: List[Dict[str, Any]] = []
        self.context: Dict[str, Any] = {}

    def set_context(
        self,
        topic: str,
        research_gaps: List[Dict],
        paper_weaknesses: List[str],
        future_directions: List[Dict]
    ):
        """Set research context for brainstorming."""
        self.context = {
            "topic": topic,
            "gaps": research_gaps,
            "weaknesses": paper_weaknesses,
            "directions": future_directions
        }

    def generate_ideas(self, num_ideas: int = 5) -> List[Dict[str, Any]]:
        """
        Generate novel research ideas based on context.

        Args:
            num_ideas: Number of ideas to generate

        Returns:
            List of research ideas with details
        """
        self.logger.info(f"Generating {num_ideas} research ideas")

        prompt = self._build_brainstorm_prompt(num_ideas)
        system = self._get_brainstorm_system()

        response = self.client.generate(
            prompt=prompt,
            system=system,
            max_tokens=8000,
            temperature=0.8  # Higher for creativity
        )

        self.ideas = self._parse_ideas(response)
        return self.ideas

    def _get_brainstorm_system(self) -> str:
        """Get system prompt for brainstorming."""
        return """You are a brilliant research advisor at a top university, helping a postgraduate student brainstorm novel research ideas for top-tier AI conferences (ACL, EMNLP, NeurIPS, ICML, AAAI, IJCAI).

Your ideas should be:
1. NOVEL - Not just incremental improvements
2. FEASIBLE - Achievable by a master's student in 6-12 months
3. IMPACTFUL - Address real problems with clear contributions
4. PUBLISHABLE - Suitable for top venues

Think creatively! Combine ideas from different areas, challenge assumptions, find overlooked problems."""

    def _build_brainstorm_prompt(self, num_ideas: int) -> str:
        """Build brainstorming prompt."""
        gaps_text = "\n".join([f"- {g.get('gap', g)}" for g in self.context.get('gaps', [])])
        weaknesses_text = "\n".join([f"- {w}" for w in self.context.get('weaknesses', [])])
        directions_text = "\n".join([f"- {d.get('direction', d)}" for d in self.context.get('directions', [])])

        return f"""Research Topic: {self.context.get('topic', 'AI Research')}

Research Gaps Identified:
{gaps_text}

Weaknesses in Current Methods:
{weaknesses_text}

Promising Future Directions:
{directions_text}

Generate {num_ideas} novel research ideas. For each idea, provide JSON:
{{
    "ideas": [
        {{
            "title": "Catchy paper title",
            "one_sentence": "One sentence summary",
            "problem": "What problem does it solve?",
            "novelty": "What's new about this approach?",
            "method_sketch": "Brief method description",
            "expected_contribution": "What will this contribute?",
            "feasibility": "high/medium/low",
            "required_resources": ["GPU", "dataset", etc.],
            "potential_venues": ["ACL", "NeurIPS", etc.],
            "risks": ["risk1", "risk2"],
            "first_steps": ["step1", "step2", "step3"]
        }}
    ]
}}"""

    def _parse_ideas(self, response: str) -> List[Dict[str, Any]]:
        """Parse ideas from AI response."""
        try:
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                return data.get("ideas", [data])
            return []
        except json.JSONDecodeError:
            return [{"raw_response": response}]

    def evaluate_idea(self, idea_index: int) -> Dict[str, Any]:
        """Evaluate feasibility of a specific idea."""
        if idea_index >= len(self.ideas):
            return {"error": "Invalid idea index"}

        idea = self.ideas[idea_index]
        prompt = f"""Evaluate this research idea critically:

Title: {idea.get('title')}
Problem: {idea.get('problem')}
Method: {idea.get('method_sketch')}

Provide evaluation:
1. Novelty score (1-10)
2. Feasibility score (1-10)
3. Impact score (1-10)
4. Main challenges
5. Suggestions to strengthen"""

        response = self.client.generate(
            prompt=prompt,
            max_tokens=2000,
            temperature=0.3
        )
        return {"idea": idea, "evaluation": response}
