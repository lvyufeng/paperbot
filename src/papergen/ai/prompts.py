"""Prompt templates for different pipeline stages."""

from typing import List, Dict, Any, Optional


class PromptLibrary:
    """Manages prompt templates for different stages."""

    @staticmethod
    def research_organization(
        sources: List[str],
        focus: str = "",
        topic: str = ""
    ) -> tuple[str, str]:
        """
        Generate prompt for organizing research sources.

        Args:
            sources: List of source texts
            focus: Optional focus areas
            topic: Research topic

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        system_prompt = """You are an expert research assistant helping to organize academic research sources.
Your task is to analyze multiple research sources and create a coherent, well-organized summary that:
- Identifies key themes and concepts
- Groups related information
- Summarizes main findings
- Identifies methodologies used
- Notes research gaps and opportunities
- Maintains academic rigor and accuracy"""

        sources_text = "\n\n---\n\n".join([f"Source {i+1}:\n{source}" for i, source in enumerate(sources)])

        user_prompt = f"""Please organize the following research sources into a comprehensive summary.

Research Topic: {topic}
{f"Focus Areas: {focus}" if focus else ""}

Sources:
{sources_text}

Create an organized research summary with these sections:
1. **Overview**: Brief overview of the research landscape
2. **Key Themes**: Main themes and concepts across sources
3. **Methodologies**: Research methodologies identified
4. **Key Findings**: Important findings and results
5. **Research Gaps**: Identified gaps and opportunities
6. **Relevant Citations**: Key papers and authors to cite

Format the output in clear, academic Markdown."""

        return system_prompt, user_prompt

    @staticmethod
    def outline_generation(
        research: str,
        topic: str,
        sections: List[str],
        word_count_targets: Optional[Dict[str, int]] = None
    ) -> tuple[str, str]:
        """
        Generate prompt for creating paper outline.

        Args:
            research: Organized research text
            topic: Paper topic
            sections: List of section names
            word_count_targets: Target word counts for sections

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        system_prompt = """You are an expert academic writer helping to create a detailed paper outline.
Your task is to design a comprehensive, logical structure for an academic paper that:
- Follows academic conventions
- Has clear objectives for each section
- Identifies key points to cover
- Suggests relevant sources for each section
- Maintains logical flow between sections
- Addresses the research question thoroughly"""

        sections_list = ", ".join(sections)

        wc_text = ""
        if word_count_targets:
            wc_text = "\n".join([f"- {sec}: {wc} words" for sec, wc in word_count_targets.items()])

        user_prompt = f"""Create a detailed outline for an academic paper on: {topic}

Sections to include: {sections_list}

{f"Target word counts:{chr(10)}{wc_text}" if wc_text else ""}

Based on this organized research:
{research[:10000]}

For each section, provide:
1. **Title**: Section name
2. **Objectives**: What this section should accomplish (2-4 objectives)
3. **Key Points**: Specific points to cover (4-8 points)
4. **Relevant Sources**: Which sources from the research to reference
5. **Notes**: Any special considerations or guidance

Output the outline in JSON format matching this structure:
{{
  "sections": [
    {{
      "id": "introduction",
      "title": "Introduction",
      "level": 1,
      "order": 0,
      "objectives": ["obj1", "obj2"],
      "key_points": ["point1", "point2"],
      "sources": ["source_1", "source_2"],
      "guidance": "special notes"
    }}
  ]
}}"""

        return system_prompt, user_prompt

    @staticmethod
    def section_drafting(
        section_title: str,
        objectives: List[str],
        key_points: List[str],
        research: str,
        guidance: str = "",
        word_count_target: int = 1000
    ) -> tuple[str, str]:
        """
        Generate prompt for drafting a section.

        Args:
            section_title: Title of the section
            objectives: Section objectives
            key_points: Key points to cover
            research: Relevant research
            guidance: Optional guidance
            word_count_target: Target word count

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        system_prompt = f"""You are an expert academic writer drafting the "{section_title}" section of a research paper.

Write in a clear, academic style that:
- Maintains scholarly tone and rigor
- Uses proper citations (format as [CITE:author_year])
- Presents ideas logically and coherently
- Supports claims with evidence
- Uses appropriate technical terminology
- Flows naturally from point to point

Target length: approximately {word_count_target} words."""

        objectives_text = "\n".join([f"- {obj}" for obj in objectives])
        key_points_text = "\n".join([f"- {point}" for point in key_points])

        user_prompt = f"""Write the {section_title} section of the paper.

**Objectives:**
{objectives_text}

**Key Points to Cover:**
{key_points_text}

{f"**Guidance:** {guidance}" if guidance else ""}

**Relevant Research:**
{research}

**Instructions:**
1. Write in academic style appropriate for scholarly publication
2. Cover all key points while maintaining logical flow
3. Include citations where appropriate using [CITE:author_year] format
4. Target approximately {word_count_target} words
5. Use clear paragraph structure with topic sentences
6. Build arguments with evidence from research

Write the complete section in Markdown format."""

        return system_prompt, user_prompt

    @staticmethod
    def section_review(section_title: str, content: str) -> tuple[str, str]:
        """
        Generate prompt for reviewing a drafted section.

        Args:
            section_title: Title of the section
            content: Section content to review

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        system_prompt = """You are an expert peer reviewer evaluating academic writing.
Provide constructive, specific feedback focusing on:
- Clarity and coherence
- Logical structure and flow
- Evidence and citation usage
- Technical accuracy
- Writing quality
- Areas for improvement"""

        user_prompt = f"""Review the following {section_title} section and provide detailed feedback.

**Section Content:**
{content}

**Provide feedback on:**
1. **Strengths**: What works well (2-3 points)
2. **Areas for Improvement**: Specific issues and suggestions (3-5 points)
3. **Structure**: Comments on organization and flow
4. **Citations**: Assessment of citation usage
5. **Clarity**: Any unclear or confusing parts
6. **Specific Suggestions**: Concrete recommendations for revision

Format your feedback in clear, actionable Markdown."""

        return system_prompt, user_prompt

    @staticmethod
    def section_revision(
        original_content: str,
        feedback: str,
        iteration: int
    ) -> tuple[str, str]:
        """
        Generate prompt for revising a section based on feedback.

        Args:
            original_content: Original section content
            feedback: Feedback to address
            iteration: Revision iteration number

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        system_prompt = f"""You are an expert academic writer revising a paper section (Revision {iteration}).

Your task is to improve the section by:
- Addressing all feedback points
- Maintaining or improving writing quality
- Preserving good elements from the original
- Ensuring coherent flow
- Strengthening weak areas"""

        user_prompt = f"""Revise the following section based on the feedback provided.

**Original Content:**
{original_content}

**Feedback to Address:**
{feedback}

**Instructions:**
1. Address each point in the feedback
2. Keep what works well from the original
3. Improve areas identified as weak
4. Maintain academic tone and quality
5. Ensure smooth transitions and flow
6. Preserve citations and add new ones where needed

Provide the complete revised section in Markdown format."""

        return system_prompt, user_prompt

    @staticmethod
    def abstract_generation(
        paper_content: Dict[str, str],
        topic: str,
        max_words: int = 250
    ) -> tuple[str, str]:
        """
        Generate prompt for creating abstract (done last).

        Args:
            paper_content: Dictionary of section content
            topic: Paper topic
            max_words: Maximum words for abstract

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        system_prompt = """You are an expert academic writer creating a paper abstract.

An effective abstract should:
- Concisely summarize the entire paper
- State the research problem/question
- Describe the methodology briefly
- Present key findings/results
- Highlight significance and contributions
- Be self-contained and informative"""

        sections_text = "\n\n".join([f"## {title}\n{content[:1000]}"
                                     for title, content in paper_content.items()])

        user_prompt = f"""Create an abstract for a paper on: {topic}

Based on the paper content:
{sections_text}

Write a compelling abstract (max {max_words} words) that:
1. States the research problem
2. Briefly describes the approach/methodology
3. Summarizes key findings
4. Highlights the contribution and significance
5. Is clear and accessible to the target audience

Output just the abstract text in academic style."""

        return system_prompt, user_prompt
