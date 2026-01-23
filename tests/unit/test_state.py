"""Tests for state management."""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import json

from papergen.core.state import (
    StageStatus,
    SourceType,
    Source,
    Section,
    Draft,
    ProjectMetadata,
    StageInfo,
    ProjectState
)


class TestStageStatus:
    """Tests for StageStatus enum."""

    def test_stage_status_values(self):
        """Test stage status values."""
        assert StageStatus.PENDING.value == "pending"
        assert StageStatus.IN_PROGRESS.value == "in_progress"
        assert StageStatus.COMPLETED.value == "completed"
        assert StageStatus.FAILED.value == "failed"


class TestSourceType:
    """Tests for SourceType enum."""

    def test_source_type_values(self):
        """Test source type values."""
        assert SourceType.PDF.value == "pdf"
        assert SourceType.WEB.value == "web"
        assert SourceType.TEXT.value == "text"
        assert SourceType.NOTE.value == "note"


class TestSource:
    """Tests for Source model."""

    def test_source_creation(self):
        """Test creating a source."""
        source = Source(
            id="source_001",
            type=SourceType.PDF,
            original_path="/path/to/paper.pdf",
            extracted_path="/path/to/extracted/source_001.json",
            added_at=datetime.now()
        )

        assert source.id == "source_001"
        assert source.type == SourceType.PDF
        assert source.extraction_status == "pending"

    def test_source_with_metadata(self):
        """Test source with metadata."""
        source = Source(
            id="source_002",
            type=SourceType.WEB,
            original_path="https://example.com/paper",
            extracted_path="/extracted/source_002.json",
            added_at=datetime.now(),
            metadata={"title": "Web Paper", "fetched": True}
        )

        assert source.metadata["title"] == "Web Paper"

    def test_source_relevance_score(self):
        """Test source with relevance score."""
        source = Source(
            id="test",
            type=SourceType.PDF,
            original_path="/path",
            extracted_path="/extracted",
            added_at=datetime.now(),
            relevance_score=0.85
        )

        assert source.relevance_score == 0.85


class TestSection:
    """Tests for Section model in state module."""

    def test_section_creation(self):
        """Test creating a section."""
        section = Section(
            id="intro",
            title="Introduction",
            level=1,
            order=1
        )

        assert section.id == "intro"
        assert section.level == 1

    def test_section_with_subsections(self):
        """Test section with subsections."""
        subsection = Section(
            id="intro_bg",
            title="Background",
            level=2,
            order=1
        )
        section = Section(
            id="intro",
            title="Introduction",
            level=1,
            order=0,
            subsections=[subsection]
        )

        assert len(section.subsections) == 1
        assert section.subsections[0].id == "intro_bg"


class TestDraft:
    """Tests for Draft model."""

    def test_draft_creation(self):
        """Test creating a draft."""
        now = datetime.now()
        draft = Draft(
            section_id="intro",
            version=1,
            created_at=now,
            updated_at=now,
            status="complete",
            content="This is the introduction content."
        )

        assert draft.section_id == "intro"
        assert draft.version == 1
        assert draft.status == "complete"

    def test_draft_with_citations(self):
        """Test draft with citations."""
        now = datetime.now()
        draft = Draft(
            section_id="lit_review",
            version=1,
            created_at=now,
            updated_at=now,
            status="complete",
            content="Content with citations",
            citations=[
                {"key": "smith2020", "location": 100},
                {"key": "doe2021", "location": 250}
            ]
        )

        assert len(draft.citations) == 2

    def test_draft_revision_history(self):
        """Test draft revision history."""
        now = datetime.now()
        draft = Draft(
            section_id="methods",
            version=3,
            created_at=now,
            updated_at=now,
            status="revised",
            content="Current content",
            revision_history=[
                {"version": 1, "date": "2024-01-01", "changes": "Initial draft"},
                {"version": 2, "date": "2024-01-05", "changes": "Added details"}
            ]
        )

        assert len(draft.revision_history) == 2


class TestProjectMetadata:
    """Tests for ProjectMetadata model."""

    def test_metadata_creation(self):
        """Test creating project metadata."""
        metadata = ProjectMetadata(
            title="Test Paper",
            authors=["John Smith", "Jane Doe"],
            keywords=["AI", "ML"],
            abstract="This is the abstract."
        )

        assert metadata.title == "Test Paper"
        assert len(metadata.authors) == 2
        assert len(metadata.keywords) == 2

    def test_metadata_defaults(self):
        """Test metadata default values."""
        metadata = ProjectMetadata()

        assert metadata.title is None
        assert metadata.authors == []
        assert metadata.keywords == []


class TestStageInfo:
    """Tests for StageInfo model."""

    def test_stage_info_creation(self):
        """Test creating stage info."""
        info = StageInfo()

        assert info.status == StageStatus.PENDING
        assert info.started_at is None
        assert info.completed_at is None

    def test_stage_info_with_times(self):
        """Test stage info with timestamps."""
        now = datetime.now()
        info = StageInfo(
            status=StageStatus.COMPLETED,
            started_at=now,
            completed_at=now
        )

        assert info.status == StageStatus.COMPLETED
        assert info.started_at is not None

    def test_stage_info_metadata(self):
        """Test stage info with metadata."""
        info = StageInfo(
            status=StageStatus.FAILED,
            metadata={"error": "API timeout", "retry_count": 3}
        )

        assert info.metadata["error"] == "API timeout"


class TestProjectState:
    """Tests for ProjectState model."""

    @pytest.fixture
    def sample_state(self):
        """Create a sample project state."""
        return ProjectState(
            project_id="test-123",
            topic="Machine Learning Research",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

    def test_state_creation(self, sample_state):
        """Test creating project state."""
        assert sample_state.project_id == "test-123"
        assert sample_state.topic == "Machine Learning Research"
        assert sample_state.current_stage == "research"
        assert sample_state.template == "ieee"

    def test_state_initializes_stages(self, sample_state):
        """Test that stages are initialized."""
        assert "research" in sample_state.stages
        assert "outline" in sample_state.stages
        assert "draft" in sample_state.stages
        assert "revise" in sample_state.stages
        assert "format" in sample_state.stages

    def test_state_custom_format(self):
        """Test state with custom format."""
        state = ProjectState(
            project_id="test",
            topic="Test",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            template="acm",
            format="markdown"
        )

        assert state.template == "acm"
        assert state.format == "markdown"


class TestProjectStateTransitions:
    """Tests for project state transitions."""

    @pytest.fixture
    def state(self):
        """Create a fresh project state."""
        return ProjectState(
            project_id="test",
            topic="Test",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

    def test_can_proceed_to_research(self, state):
        """Test can proceed to research stage."""
        assert state.can_proceed_to("research") is True

    def test_cannot_skip_stages(self, state):
        """Test cannot skip stages."""
        # Cannot go directly to draft without completing research and outline
        assert state.can_proceed_to("draft") is False

    def test_can_proceed_after_completion(self, state):
        """Test can proceed after completing stage."""
        state.mark_stage_started("research")
        state.mark_stage_completed("research")

        assert state.can_proceed_to("outline") is True

    def test_cannot_proceed_to_unknown_stage(self, state):
        """Test cannot proceed to unknown stage."""
        assert state.can_proceed_to("unknown") is False

    def test_mark_stage_started(self, state):
        """Test marking stage as started."""
        state.mark_stage_started("research")

        assert state.stages["research"].status == StageStatus.IN_PROGRESS
        assert state.stages["research"].started_at is not None
        assert state.current_stage == "research"

    def test_mark_stage_completed(self, state):
        """Test marking stage as completed."""
        state.mark_stage_started("research")
        state.mark_stage_completed("research")

        assert state.stages["research"].status == StageStatus.COMPLETED
        assert state.stages["research"].completed_at is not None

    def test_mark_stage_failed(self, state):
        """Test marking stage as failed."""
        state.mark_stage_started("research")
        state.mark_stage_failed("research", "API error")

        assert state.stages["research"].status == StageStatus.FAILED
        assert state.stages["research"].metadata["error"] == "API error"

    def test_mark_creates_stage_if_missing(self):
        """Test that marking creates stage info if missing."""
        state = ProjectState(
            project_id="test",
            topic="Test",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        # Remove a stage
        del state.stages["research"]

        state.mark_stage_started("research")

        assert "research" in state.stages
        assert state.stages["research"].status == StageStatus.IN_PROGRESS


class TestProjectStatePersistence:
    """Tests for saving and loading state."""

    def test_save_and_load(self):
        """Test saving and loading state."""
        state = ProjectState(
            project_id="test-save",
            topic="Save Test",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata=ProjectMetadata(
                title="Test Paper",
                authors=["Author"]
            )
        )
        state.mark_stage_started("research")
        state.mark_stage_completed("research")

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "state.json"
            state.save(path)

            # Verify file exists
            assert path.exists()

            # Load and verify
            loaded = ProjectState.load(path)

            assert loaded.project_id == "test-save"
            assert loaded.topic == "Save Test"
            assert loaded.metadata.title == "Test Paper"
            assert loaded.stages["research"].status == StageStatus.COMPLETED

    def test_save_creates_directory(self):
        """Test that save creates parent directory."""
        state = ProjectState(
            project_id="test",
            topic="Test",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "nested" / "dir" / "state.json"
            state.save(path)

            assert path.exists()


class TestProjectStateGetStatus:
    """Tests for get_stage_status method."""

    def test_get_stage_status_existing(self):
        """Test getting status of existing stage."""
        state = ProjectState(
            project_id="test",
            topic="Test",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        state.mark_stage_started("research")

        status = state.get_stage_status("research")
        assert status == StageStatus.IN_PROGRESS

    def test_get_stage_status_nonexistent(self):
        """Test getting status of nonexistent stage."""
        state = ProjectState(
            project_id="test",
            topic="Test",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Remove a stage to test
        del state.stages["research"]

        status = state.get_stage_status("research")
        assert status == StageStatus.PENDING
