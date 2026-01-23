"""Tests for PromptLibrary."""

import pytest

from papergen.ai.prompts import PromptLibrary


class TestResearchOrganization:
    """Tests for research organization prompts."""

    def test_basic_generation(self):
        """Test basic prompt generation."""
        sources = ["Source 1 content", "Source 2 content"]
        system, user = PromptLibrary.research_organization(sources)

        assert "research assistant" in system.lower()
        assert "Source 1" in user
        assert "Source 2" in user

    def test_with_focus_and_topic(self):
        """Test with focus and topic."""
        sources = ["Content"]
        system, user = PromptLibrary.research_organization(
            sources, focus="methodology", topic="Machine Learning"
        )

        assert "Machine Learning" in user
        assert "methodology" in user.lower()

    def test_empty_sources(self):
        """Test with empty sources."""
        system, user = PromptLibrary.research_organization([])

        assert system != ""
        assert user != ""


class TestOutlineGeneration:
    """Tests for outline generation prompts."""

    def test_basic_generation(self):
        """Test basic outline prompt."""
        system, user = PromptLibrary.outline_generation(
            research="Research text",
            topic="AI",
            sections=["Introduction", "Methods"]
        )

        assert "outline" in system.lower()
        assert "AI" in user
        assert "Introduction" in user
        assert "Methods" in user

    def test_with_word_count_targets(self):
        """Test with word count targets."""
        system, user = PromptLibrary.outline_generation(
            research="Research",
            topic="Test",
            sections=["Intro"],
            word_count_targets={"Intro": 500}
        )

        assert "500 words" in user

    def test_json_format_requested(self):
        """Test that JSON format is requested."""
        system, user = PromptLibrary.outline_generation(
            research="Research",
            topic="Test",
            sections=["Intro"]
        )

        assert "JSON" in user


class TestSectionDrafting:
    """Tests for section drafting prompts."""

    def test_basic_generation(self):
        """Test basic drafting prompt."""
        system, user = PromptLibrary.section_drafting(
            section_title="Introduction",
            objectives=["Explain the problem", "Present motivation"],
            key_points=["Point 1", "Point 2"],
            research="Research text",
            word_count_target=1000
        )

        assert "Introduction" in system
        assert "1000" in system
        assert "Explain the problem" in user
        assert "Point 1" in user

    def test_with_guidance(self):
        """Test with additional guidance."""
        system, user = PromptLibrary.section_drafting(
            section_title="Methods",
            objectives=["Describe approach"],
            key_points=["Algorithm"],
            research="Research",
            guidance="Focus on clarity"
        )

        assert "Focus on clarity" in user

    def test_citation_format_specified(self):
        """Test that citation format is specified."""
        system, user = PromptLibrary.section_drafting(
            section_title="Test",
            objectives=[],
            key_points=[],
            research="Research"
        )

        assert "CITE:" in system or "CITE:" in user


class TestSectionReview:
    """Tests for section review prompts."""

    def test_basic_generation(self):
        """Test basic review prompt."""
        system, user = PromptLibrary.section_review(
            section_title="Introduction",
            content="This is the section content."
        )

        assert "reviewer" in system.lower()
        assert "Introduction" in user
        assert "section content" in user

    def test_feedback_categories(self):
        """Test that feedback categories are requested."""
        system, user = PromptLibrary.section_review("Test", "Content")

        assert "Strengths" in user
        assert "Improvement" in user
        assert "Citations" in user


class TestSectionRevision:
    """Tests for section revision prompts."""

    def test_basic_generation(self):
        """Test basic revision prompt."""
        system, user = PromptLibrary.section_revision(
            original_content="Original text",
            feedback="Improve clarity",
            iteration=2
        )

        assert "Revision 2" in system
        assert "Original text" in user
        assert "Improve clarity" in user

    def test_iteration_tracking(self):
        """Test iteration tracking."""
        system1, _ = PromptLibrary.section_revision("Content", "Feedback", 1)
        system3, _ = PromptLibrary.section_revision("Content", "Feedback", 3)

        assert "Revision 1" in system1
        assert "Revision 3" in system3


class TestAbstractGeneration:
    """Tests for abstract generation prompts."""

    def test_basic_generation(self):
        """Test basic abstract prompt."""
        paper_content = {
            "Introduction": "Intro text",
            "Methods": "Methods text"
        }

        system, user = PromptLibrary.abstract_generation(
            paper_content=paper_content,
            topic="Machine Learning"
        )

        assert "abstract" in system.lower()
        assert "Machine Learning" in user
        assert "Introduction" in user or "Intro text" in user

    def test_max_words_specified(self):
        """Test that max words is specified."""
        system, user = PromptLibrary.abstract_generation(
            paper_content={"Intro": "Text"},
            topic="Test",
            max_words=300
        )

        assert "300" in user

    def test_content_truncation(self):
        """Test that long content is truncated."""
        long_content = {"Section": "x" * 5000}

        system, user = PromptLibrary.abstract_generation(
            paper_content=long_content,
            topic="Test"
        )

        # Content should be truncated to 1000 chars per section
        assert len(user) < 6000
