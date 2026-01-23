"""Tests for section management and drafting."""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from datetime import datetime
import tempfile
import json

from papergen.document.section import SectionDraft, SectionManager
from papergen.document.outline import Section


class TestSectionDraft:
    """Tests for SectionDraft model."""

    def test_section_draft_creation(self):
        """Test creating a section draft."""
        draft = SectionDraft(
            section_id="intro",
            content="This is the introduction content.",
            version=1
        )

        assert draft.section_id == "intro"
        assert draft.content == "This is the introduction content."
        assert draft.version == 1
        assert draft.word_count == 5  # "This is the introduction content."

    def test_section_draft_word_count(self):
        """Test automatic word count calculation."""
        content = "One two three four five six seven eight nine ten"
        draft = SectionDraft(section_id="test", content=content)

        assert draft.word_count == 10

    def test_section_draft_metadata(self):
        """Test draft with metadata."""
        draft = SectionDraft(
            section_id="methods",
            content="Methods content",
            metadata={"section_title": "Methods", "ai_model": "claude"}
        )

        assert draft.metadata["section_title"] == "Methods"
        assert draft.metadata["ai_model"] == "claude"

    def test_section_draft_to_dict(self):
        """Test converting draft to dictionary."""
        draft = SectionDraft(
            section_id="results",
            content="Results here",
            version=2,
            metadata={"key": "value"}
        )

        data = draft.to_dict()

        assert data["section_id"] == "results"
        assert data["content"] == "Results here"
        assert data["version"] == 2
        assert data["word_count"] == 2
        assert data["metadata"]["key"] == "value"
        assert "created_at" in data
        assert "updated_at" in data

    def test_section_draft_from_dict(self):
        """Test creating draft from dictionary."""
        data = {
            "section_id": "conclusion",
            "content": "Conclusion text",
            "version": 3,
            "created_at": "2024-01-15T10:00:00",
            "updated_at": "2024-01-15T12:00:00",
            "metadata": {"edited": True},
            "word_count": 2,
            "citation_keys": ["smith2020"]
        }

        draft = SectionDraft.from_dict(data)

        assert draft.section_id == "conclusion"
        assert draft.version == 3
        assert draft.metadata["edited"] is True
        assert draft.citation_keys == ["smith2020"]

    def test_section_draft_timestamps(self):
        """Test that timestamps are set correctly."""
        draft = SectionDraft(section_id="test", content="content")

        assert isinstance(draft.created_at, datetime)
        assert isinstance(draft.updated_at, datetime)


class TestSectionManager:
    """Tests for SectionManager."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def section_manager(self, temp_project):
        """Create a SectionManager with temp directory."""
        return SectionManager(project_root=temp_project)

    @pytest.fixture
    def sample_section(self):
        """Create a sample section."""
        return Section(
            id="intro",
            title="Introduction",
            objectives=["Introduce topic"],
            key_points=["Background", "Motivation"],
            word_count_target=1500
        )

    def test_manager_initialization(self, temp_project):
        """Test SectionManager initialization."""
        manager = SectionManager(project_root=temp_project)

        assert manager.project_root == temp_project
        assert manager.drafts_dir.exists()
        assert manager.versions_dir.exists()

    def test_manager_with_claude_client(self, temp_project):
        """Test initialization with Claude client."""
        mock_client = Mock()
        manager = SectionManager(project_root=temp_project, claude_client=mock_client)

        assert manager.claude_client == mock_client

    def test_save_draft(self, section_manager):
        """Test saving a draft."""
        draft = SectionDraft(
            section_id="intro",
            content="Introduction content here",
            version=1
        )

        path = section_manager.save_draft(draft)

        assert path.exists()
        assert (section_manager.drafts_dir / "intro.md").exists()
        assert (section_manager.drafts_dir / "intro.json").exists()
        assert (section_manager.versions_dir / "intro_v1.md").exists()

    def test_load_draft(self, section_manager):
        """Test loading a draft."""
        # Save first
        draft = SectionDraft(
            section_id="methods",
            content="Methods content",
            version=1,
            metadata={"section_title": "Methods"}
        )
        section_manager.save_draft(draft)

        # Load
        loaded = section_manager.load_draft("methods")

        assert loaded is not None
        assert loaded.section_id == "methods"
        assert loaded.content == "Methods content"
        assert loaded.metadata["section_title"] == "Methods"

    def test_load_draft_not_found(self, section_manager):
        """Test loading nonexistent draft."""
        loaded = section_manager.load_draft("nonexistent")
        assert loaded is None

    def test_get_draft_content(self, section_manager):
        """Test getting draft content as string."""
        draft = SectionDraft(section_id="results", content="Results content")
        section_manager.save_draft(draft)

        content = section_manager.get_draft_content("results")

        assert content == "Results content"

    def test_get_draft_content_not_found(self, section_manager):
        """Test getting content of nonexistent draft."""
        content = section_manager.get_draft_content("nonexistent")
        assert content is None

    def test_list_drafts(self, section_manager):
        """Test listing all drafts."""
        # Save multiple drafts
        for section_id in ["intro", "methods", "results"]:
            draft = SectionDraft(section_id=section_id, content=f"{section_id} content")
            section_manager.save_draft(draft)

        drafts = section_manager.list_drafts()

        assert len(drafts) == 3
        assert "intro" in drafts
        assert "methods" in drafts
        assert "results" in drafts

    def test_list_drafts_empty(self, section_manager):
        """Test listing drafts when none exist."""
        drafts = section_manager.list_drafts()
        assert drafts == []

    def test_get_version_history(self, section_manager):
        """Test getting version history."""
        # Create multiple versions
        for v in [1, 2, 3]:
            draft = SectionDraft(section_id="intro", content=f"Version {v}", version=v)
            section_manager.save_draft(draft)

        versions = section_manager.get_version_history("intro")

        assert versions == [1, 2, 3]

    def test_update_draft(self, section_manager):
        """Test updating a draft."""
        # Create initial draft
        draft = SectionDraft(
            section_id="intro",
            content="Original content",
            version=1,
            metadata={"section_title": "Introduction"}
        )
        section_manager.save_draft(draft)

        # Update
        updated = section_manager.update_draft("intro", "Updated content")

        assert updated.content == "Updated content"
        assert updated.version == 2
        assert updated.metadata["section_title"] == "Introduction"

        # Verify saved
        loaded = section_manager.load_draft("intro")
        assert loaded.content == "Updated content"
        assert loaded.version == 2

    def test_update_draft_no_increment(self, section_manager):
        """Test updating without incrementing version."""
        draft = SectionDraft(section_id="intro", content="Original", version=1)
        section_manager.save_draft(draft)

        updated = section_manager.update_draft("intro", "New content", increment_version=False)

        assert updated.version == 1

    def test_draft_section_with_ai(self, section_manager, sample_section):
        """Test drafting section with AI."""
        mock_client = Mock()
        mock_client.generate.return_value = "AI generated introduction content"
        section_manager.claude_client = mock_client

        with patch('papergen.ai.prompts.PromptLibrary') as mock_prompts:
            mock_prompts.section_drafting.return_value = ("system", "user")

            draft = section_manager.draft_section(
                section=sample_section,
                research_text="Research content here"
            )

        assert draft.section_id == "intro"
        assert draft.content == "AI generated introduction content"
        mock_client.generate.assert_called_once()

    def test_draft_section_without_client_raises(self, section_manager, sample_section):
        """Test that drafting without Claude client raises error."""
        with pytest.raises(ValueError) as exc_info:
            section_manager.draft_section(
                section=sample_section,
                research_text="content"
            )

        assert "Claude client required" in str(exc_info.value)

    def test_get_statistics(self, section_manager):
        """Test getting drafting statistics."""
        # Save drafts with different word counts
        for section_id, word_count in [("intro", 100), ("methods", 200)]:
            content = " ".join(["word"] * word_count)
            draft = SectionDraft(section_id=section_id, content=content)
            draft.citation_keys = ["ref1"] if section_id == "intro" else ["ref2", "ref3"]
            section_manager.save_draft(draft)

        stats = section_manager.get_statistics()

        assert stats["sections_drafted"] == 2
        assert stats["total_words"] == 300
        assert stats["average_words_per_section"] == 150


class TestSectionManagerWithCitations:
    """Tests for SectionManager citation handling."""

    @pytest.fixture
    def manager_with_citations(self):
        """Create manager with mocked citation manager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_citation_manager = Mock()
            mock_citation_manager.extract_citations_from_text.return_value = ["smith2020", "jones2021"]

            manager = SectionManager(
                project_root=Path(tmpdir),
                citation_manager=mock_citation_manager
            )
            yield manager

    def test_draft_extracts_citations(self, manager_with_citations):
        """Test that drafting extracts citations."""
        mock_client = Mock()
        mock_client.generate.return_value = "Content with \\cite{smith2020} and \\cite{jones2021}"
        manager_with_citations.claude_client = mock_client

        section = Section(id="lit", title="Literature Review")

        with patch('papergen.ai.prompts.PromptLibrary') as mock_prompts:
            mock_prompts.section_drafting.return_value = ("system", "user")

            draft = manager_with_citations.draft_section(
                section=section,
                research_text="Research"
            )

        assert "smith2020" in draft.citation_keys
        assert "jones2021" in draft.citation_keys

    def test_update_extracts_citations(self, manager_with_citations):
        """Test that updating extracts citations."""
        # Create initial draft
        draft = SectionDraft(section_id="test", content="Initial")
        manager_with_citations.save_draft(draft)

        # Update
        updated = manager_with_citations.update_draft("test", "New content with citations")

        assert "smith2020" in updated.citation_keys
