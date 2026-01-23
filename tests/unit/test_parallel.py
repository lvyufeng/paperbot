"""Tests for parallel section drafting."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import ThreadPoolExecutor
import threading

from papergen.document.parallel import (
    DraftTask,
    DraftResult,
    ParallelSectionManager,
    BatchDraftingStrategy,
    estimate_speedup
)
from papergen.document.outline import Section
from papergen.document.section import SectionDraft


class TestDraftTask:
    """Tests for DraftTask dataclass."""

    def test_draft_task_creation(self):
        """Test creating a DraftTask."""
        section = Section(id="intro", title="Introduction")
        task = DraftTask(
            section=section,
            research_text="Research content",
            guidance="Write clearly",
            priority=5
        )

        assert task.section == section
        assert task.research_text == "Research content"
        assert task.guidance == "Write clearly"
        assert task.priority == 5

    def test_draft_task_defaults(self):
        """Test DraftTask default values."""
        section = Section(id="test", title="Test")
        task = DraftTask(section=section, research_text="content")

        assert task.guidance == ""
        assert task.priority == 0


class TestDraftResult:
    """Tests for DraftResult dataclass."""

    def test_draft_result_success(self):
        """Test successful DraftResult."""
        draft = SectionDraft(section_id="intro", content="Content")
        result = DraftResult(
            section_id="intro",
            draft=draft,
            success=True,
            duration_seconds=5.5
        )

        assert result.section_id == "intro"
        assert result.draft == draft
        assert result.success is True
        assert result.error is None
        assert result.duration_seconds == 5.5

    def test_draft_result_failure(self):
        """Test failed DraftResult."""
        result = DraftResult(
            section_id="methods",
            draft=None,
            success=False,
            error="API timeout",
            duration_seconds=30.0
        )

        assert result.success is False
        assert result.error == "API timeout"
        assert result.draft is None


class TestParallelSectionManager:
    """Tests for ParallelSectionManager."""

    @pytest.fixture
    def mock_section_manager(self):
        """Create a mocked SectionManager."""
        manager = Mock()
        manager.get_draft_content.return_value = None  # No existing drafts
        manager.draft_section.return_value = SectionDraft(
            section_id="test",
            content="Drafted content"
        )
        manager.save_draft.return_value = None
        return manager

    def test_init(self, mock_section_manager):
        """Test ParallelSectionManager initialization."""
        parallel_manager = ParallelSectionManager(
            section_manager=mock_section_manager,
            max_workers=4
        )

        assert parallel_manager.max_workers == 4
        assert parallel_manager.section_manager == mock_section_manager

    def test_init_with_progress_callback(self, mock_section_manager):
        """Test initialization with progress callback."""
        callback = Mock()
        parallel_manager = ParallelSectionManager(
            section_manager=mock_section_manager,
            progress_callback=callback
        )

        assert parallel_manager.progress_callback == callback

    def test_draft_sections_parallel_empty_tasks(self, mock_section_manager):
        """Test with empty task list."""
        parallel_manager = ParallelSectionManager(mock_section_manager)
        results = parallel_manager.draft_sections_parallel([])

        assert results == {}

    def test_draft_sections_parallel_single_task(self, mock_section_manager):
        """Test with a single task."""
        section = Section(id="intro", title="Introduction")
        task = DraftTask(section=section, research_text="Research")

        parallel_manager = ParallelSectionManager(mock_section_manager, max_workers=1)
        results = parallel_manager.draft_sections_parallel([task])

        assert "intro" in results
        assert results["intro"].success is True
        mock_section_manager.draft_section.assert_called_once()

    def test_draft_sections_parallel_multiple_tasks(self, mock_section_manager):
        """Test with multiple tasks."""
        sections = [
            Section(id="intro", title="Introduction"),
            Section(id="methods", title="Methods"),
            Section(id="results", title="Results")
        ]
        tasks = [
            DraftTask(section=s, research_text="Research")
            for s in sections
        ]

        # Return different drafts for each section
        def mock_draft(section, research_text, guidance=""):
            return SectionDraft(section_id=section.id, content=f"Content for {section.id}")

        mock_section_manager.draft_section.side_effect = mock_draft

        parallel_manager = ParallelSectionManager(mock_section_manager, max_workers=3)
        results = parallel_manager.draft_sections_parallel(tasks)

        assert len(results) == 3
        assert all(r.success for r in results.values())
        assert mock_section_manager.draft_section.call_count == 3

    def test_draft_sections_skip_existing(self, mock_section_manager):
        """Test skipping existing drafts."""
        # intro has existing draft
        mock_section_manager.get_draft_content.side_effect = lambda sid: \
            "existing" if sid == "intro" else None

        sections = [
            Section(id="intro", title="Introduction"),
            Section(id="methods", title="Methods")
        ]
        tasks = [
            DraftTask(section=s, research_text="Research")
            for s in sections
        ]

        parallel_manager = ParallelSectionManager(mock_section_manager)
        results = parallel_manager.draft_sections_parallel(tasks, skip_existing=True)

        # intro should be skipped
        assert "intro" in results
        assert results["intro"].error == "Skipped (already exists)"
        # Only methods should be drafted
        assert mock_section_manager.draft_section.call_count == 1

    def test_draft_sections_handles_failure(self, mock_section_manager):
        """Test handling of task failures."""
        def mock_draft(section, research_text, guidance=""):
            if section.id == "methods":
                raise Exception("API error")
            return SectionDraft(section_id=section.id, content="Content")

        mock_section_manager.draft_section.side_effect = mock_draft

        sections = [
            Section(id="intro", title="Introduction"),
            Section(id="methods", title="Methods")
        ]
        tasks = [
            DraftTask(section=s, research_text="Research")
            for s in sections
        ]

        parallel_manager = ParallelSectionManager(mock_section_manager, max_workers=2)
        results = parallel_manager.draft_sections_parallel(tasks)

        assert results["intro"].success is True
        assert results["methods"].success is False
        assert "API error" in results["methods"].error

    def test_progress_callback_called(self, mock_section_manager):
        """Test that progress callback is invoked."""
        progress_calls = []

        def track_progress(section_id, progress):
            progress_calls.append((section_id, progress))

        section = Section(id="intro", title="Introduction")
        task = DraftTask(section=section, research_text="Research")

        parallel_manager = ParallelSectionManager(
            mock_section_manager,
            progress_callback=track_progress
        )
        parallel_manager.draft_sections_parallel([task])

        assert len(progress_calls) == 1
        assert progress_calls[0][0] == "intro"
        assert progress_calls[0][1] == 1.0  # 100% progress

    def test_priority_ordering(self, mock_section_manager):
        """Test that tasks are sorted by priority."""
        call_order = []

        def mock_draft(section, research_text, guidance=""):
            call_order.append(section.id)
            return SectionDraft(section_id=section.id, content="Content")

        mock_section_manager.draft_section.side_effect = mock_draft

        sections = [
            Section(id="low", title="Low Priority"),
            Section(id="high", title="High Priority"),
            Section(id="medium", title="Medium Priority")
        ]
        tasks = [
            DraftTask(section=sections[0], research_text="R", priority=1),
            DraftTask(section=sections[1], research_text="R", priority=10),
            DraftTask(section=sections[2], research_text="R", priority=5)
        ]

        # Use 1 worker to ensure sequential execution
        parallel_manager = ParallelSectionManager(mock_section_manager, max_workers=1)
        parallel_manager.draft_sections_parallel(tasks)

        # High priority should be first
        assert call_order[0] == "high"


class TestParallelSectionManagerStatistics:
    """Tests for statistics gathering."""

    @pytest.fixture
    def manager_with_results(self):
        """Create manager with pre-populated results."""
        mock_sm = Mock()
        mock_sm.get_draft_content.return_value = None

        parallel_manager = ParallelSectionManager(mock_sm)
        parallel_manager._results = {
            "intro": DraftResult(
                section_id="intro",
                draft=SectionDraft(section_id="intro", content="Content"),
                success=True,
                duration_seconds=10.0
            ),
            "methods": DraftResult(
                section_id="methods",
                draft=SectionDraft(section_id="methods", content="Content"),
                success=True,
                duration_seconds=15.0
            ),
            "results": DraftResult(
                section_id="results",
                draft=None,
                success=False,
                error="Failed",
                duration_seconds=5.0
            ),
            "abstract": DraftResult(
                section_id="abstract",
                draft=None,
                success=True,
                error="Skipped (already exists)"
            )
        }
        return parallel_manager

    def test_get_statistics(self, manager_with_results):
        """Test statistics calculation."""
        stats = manager_with_results.get_statistics()

        assert stats["total_sections"] == 4
        assert stats["successful"] == 2  # intro, methods
        assert stats["failed"] == 1  # results
        assert stats["skipped"] == 1  # abstract
        assert stats["total_duration"] == 25.0  # 10 + 15
        assert stats["average_duration"] == 12.5

    def test_get_statistics_empty(self):
        """Test statistics with no results."""
        mock_sm = Mock()
        parallel_manager = ParallelSectionManager(mock_sm)

        stats = parallel_manager.get_statistics()

        assert stats["total_sections"] == 0
        assert stats["successful"] == 0
        assert stats["total_duration"] == 0.0


class TestBatchDraftingStrategy:
    """Tests for BatchDraftingStrategy."""

    def test_by_size(self):
        """Test batching by fixed size."""
        sections = [
            Section(id=f"s{i}", title=f"Section {i}")
            for i in range(7)
        ]

        batches = BatchDraftingStrategy.by_size(sections, batch_size=3)

        assert len(batches) == 3
        assert len(batches[0]) == 3
        assert len(batches[1]) == 3
        assert len(batches[2]) == 1

    def test_by_size_exact_fit(self):
        """Test batching when sections divide evenly."""
        sections = [
            Section(id=f"s{i}", title=f"Section {i}")
            for i in range(6)
        ]

        batches = BatchDraftingStrategy.by_size(sections, batch_size=2)

        assert len(batches) == 3
        assert all(len(b) == 2 for b in batches)

    def test_by_priority(self):
        """Test batching by priority."""
        sections = [
            Section(id="s1", title="S1"),
            Section(id="s2", title="S2"),
            Section(id="s3", title="S3"),
            Section(id="s4", title="S4")
        ]
        priorities = {"s1": 1, "s2": 3, "s3": 3, "s4": 2}

        batches = BatchDraftingStrategy.by_priority(sections, priorities)

        # Highest priority first
        assert len(batches) == 3
        # Priority 3 batch (s2, s3)
        assert {s.id for s in batches[0]} == {"s2", "s3"}
        # Priority 2 batch (s4)
        assert batches[1][0].id == "s4"
        # Priority 1 batch (s1)
        assert batches[2][0].id == "s1"

    def test_by_depth(self):
        """Test batching by depth level."""
        sections = [
            Mock(id="s1", depth=0),
            Mock(id="s2", depth=1),
            Mock(id="s3", depth=1),
            Mock(id="s4", depth=2)
        ]

        batches = BatchDraftingStrategy.by_depth(sections)

        assert len(batches) == 3
        # Depth 0 first
        assert batches[0][0].id == "s1"
        # Depth 1
        assert {s.id for s in batches[1]} == {"s2", "s3"}
        # Depth 2
        assert batches[2][0].id == "s4"

    def test_by_depth_without_depth_attr(self):
        """Test batching when sections lack depth attribute."""
        sections = [
            Section(id="s1", title="S1"),
            Section(id="s2", title="S2")
        ]

        batches = BatchDraftingStrategy.by_depth(sections)

        # All should be in depth 0 batch
        assert len(batches) == 1
        assert len(batches[0]) == 2


class TestEstimateSpeedup:
    """Tests for speedup estimation."""

    def test_estimate_speedup_basic(self):
        """Test basic speedup estimation."""
        result = estimate_speedup(num_sections=6, max_workers=3)

        assert result["num_sections"] == 6
        assert result["max_workers"] == 3
        assert result["sequential_time_seconds"] == 360.0  # 6 * 60
        assert result["speedup"] > 1.0

    def test_estimate_speedup_single_section(self):
        """Test speedup with single section."""
        result = estimate_speedup(num_sections=1, max_workers=3)

        assert result["num_sections"] == 1
        assert result["speedup"] < 1.1  # Minimal speedup

    def test_estimate_speedup_many_sections(self):
        """Test speedup with many sections."""
        result = estimate_speedup(num_sections=12, max_workers=4)

        # Should have significant speedup
        assert result["speedup"] > 2.0
        assert result["time_saved_minutes"] > 0

    def test_estimate_speedup_returns_all_keys(self):
        """Test that all expected keys are returned."""
        result = estimate_speedup(num_sections=5, max_workers=2)

        expected_keys = [
            "num_sections",
            "max_workers",
            "sequential_time_seconds",
            "parallel_time_seconds",
            "speedup",
            "time_saved_seconds",
            "time_saved_minutes"
        ]

        for key in expected_keys:
            assert key in result


class TestThreadSafety:
    """Tests for thread safety of ParallelSectionManager."""

    def test_concurrent_result_collection(self):
        """Test that results are collected thread-safely."""
        mock_sm = Mock()
        mock_sm.get_draft_content.return_value = None

        # Simulate concurrent drafting with delays
        def slow_draft(section, research_text, guidance=""):
            import time
            time.sleep(0.01)  # Small delay to allow concurrency
            return SectionDraft(section_id=section.id, content="Content")

        mock_sm.draft_section.side_effect = slow_draft

        sections = [Section(id=f"s{i}", title=f"S{i}") for i in range(10)]
        tasks = [DraftTask(section=s, research_text="R") for s in sections]

        parallel_manager = ParallelSectionManager(mock_sm, max_workers=5)
        results = parallel_manager.draft_sections_parallel(tasks)

        # All results should be collected
        assert len(results) == 10
        assert all(results[f"s{i}"].success for i in range(10))
