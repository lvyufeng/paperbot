"""Parallel section drafting for faster paper generation.

This module provides parallel execution of section drafting using ThreadPoolExecutor,
enabling 3-5x faster paper generation when drafting multiple sections.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from typing import List, Dict, Optional, Callable, Any
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import threading

from ..document.outline import Section
from ..document.section import SectionDraft, SectionManager
from ..core.logging_config import get_logger


@dataclass
class DraftTask:
    """Represents a section drafting task."""
    section: Section
    research_text: str
    guidance: str = ""
    priority: int = 0  # Higher priority sections drafted first


@dataclass
class DraftResult:
    """Result of a drafting task."""
    section_id: str
    draft: Optional[SectionDraft]
    success: bool
    error: Optional[str] = None
    duration_seconds: float = 0.0


class ParallelSectionManager:
    """Manages parallel section drafting with progress tracking."""

    def __init__(
        self,
        section_manager: SectionManager,
        max_workers: int = 3,
        progress_callback: Optional[Callable[[str, float], None]] = None
    ):
        """
        Initialize parallel section manager.

        Args:
            section_manager: Base section manager
            max_workers: Maximum number of parallel workers (default: 3)
            progress_callback: Optional callback for progress updates (section_id, progress)
        """
        self.section_manager = section_manager
        self.max_workers = max_workers
        self.progress_callback = progress_callback
        self.logger = get_logger()

        # Thread-safe progress tracking
        self._lock = threading.Lock()
        self._completed = 0
        self._total = 0
        self._results: Dict[str, DraftResult] = {}

    def draft_sections_parallel(
        self,
        tasks: List[DraftTask],
        skip_existing: bool = True
    ) -> Dict[str, DraftResult]:
        """
        Draft multiple sections in parallel.

        Args:
            tasks: List of DraftTask objects
            skip_existing: Skip sections that already have drafts

        Returns:
            Dictionary mapping section_id to DraftResult
        """
        # Filter tasks if skip_existing
        if skip_existing:
            filtered_tasks = []
            for task in tasks:
                if self.section_manager.get_draft_content(task.section.id):
                    self.logger.info(f"Skipping {task.section.id} (already drafted)")
                    self._results[task.section.id] = DraftResult(
                        section_id=task.section.id,
                        draft=None,
                        success=True,
                        error="Skipped (already exists)"
                    )
                else:
                    filtered_tasks.append(task)
            tasks = filtered_tasks

        if not tasks:
            self.logger.info("No sections to draft")
            return self._results

        # Sort by priority (higher first)
        tasks.sort(key=lambda t: t.priority, reverse=True)

        self._total = len(tasks)
        self._completed = 0

        self.logger.info(f"Starting parallel drafting of {self._total} sections with {self.max_workers} workers")

        # Create thread pool and submit tasks
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(self._draft_section_task, task): task
                for task in tasks
            }

            # Process completed tasks
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = future.result()
                    self._results[result.section_id] = result

                    with self._lock:
                        self._completed += 1
                        progress = self._completed / self._total

                    if self.progress_callback:
                        self.progress_callback(result.section_id, progress)

                    if result.success:
                        self.logger.info(
                            f"Completed {result.section_id} "
                            f"({self._completed}/{self._total}) "
                            f"in {result.duration_seconds:.1f}s"
                        )
                    else:
                        self.logger.error(
                            f"Failed {result.section_id}: {result.error}"
                        )

                except Exception as e:
                    self.logger.error(f"Unexpected error for {task.section.id}: {e}")
                    self._results[task.section.id] = DraftResult(
                        section_id=task.section.id,
                        draft=None,
                        success=False,
                        error=str(e)
                    )

        return self._results

    def _draft_section_task(self, task: DraftTask) -> DraftResult:
        """
        Draft a single section (executed in thread).

        Args:
            task: DraftTask to execute

        Returns:
            DraftResult
        """
        start_time = datetime.now()
        section_id = task.section.id

        try:
            self.logger.debug(f"Starting draft for {section_id}")

            # Draft the section
            draft = self.section_manager.draft_section(
                section=task.section,
                research_text=task.research_text,
                guidance=task.guidance
            )

            # Save the draft
            self.section_manager.save_draft(draft)

            duration = (datetime.now() - start_time).total_seconds()

            return DraftResult(
                section_id=section_id,
                draft=draft,
                success=True,
                duration_seconds=duration
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error drafting {section_id}: {e}")

            return DraftResult(
                section_id=section_id,
                draft=None,
                success=False,
                error=str(e),
                duration_seconds=duration
            )

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the parallel drafting session.

        Returns:
            Dictionary with statistics
        """
        if not self._results:
            return {
                "total_sections": 0,
                "successful": 0,
                "failed": 0,
                "skipped": 0,
                "total_duration": 0.0,
                "average_duration": 0.0
            }

        successful = [r for r in self._results.values() if r.success and r.draft]
        failed = [r for r in self._results.values() if not r.success]
        skipped = [r for r in self._results.values() if r.success and not r.draft]

        total_duration = sum(r.duration_seconds for r in successful)
        avg_duration = total_duration / len(successful) if successful else 0.0

        return {
            "total_sections": len(self._results),
            "successful": len(successful),
            "failed": len(failed),
            "skipped": len(skipped),
            "total_duration": total_duration,
            "average_duration": avg_duration,
            "success_rate": len(successful) / len(self._results) * 100 if self._results else 0.0
        }


class BatchDraftingStrategy:
    """Strategies for batching sections for parallel drafting."""

    @staticmethod
    def by_depth(sections: List[Section]) -> List[List[Section]]:
        """
        Batch sections by depth level.

        Sections at the same depth can be drafted in parallel.

        Args:
            sections: List of sections

        Returns:
            List of batches (each batch can be drafted in parallel)
        """
        depth_map: Dict[int, List[Section]] = {}

        for section in sections:
            depth = section.depth if hasattr(section, 'depth') else 0
            if depth not in depth_map:
                depth_map[depth] = []
            depth_map[depth].append(section)

        # Return batches sorted by depth
        return [depth_map[d] for d in sorted(depth_map.keys())]

    @staticmethod
    def by_size(sections: List[Section], batch_size: int = 3) -> List[List[Section]]:
        """
        Batch sections by fixed size.

        Args:
            sections: List of sections
            batch_size: Number of sections per batch

        Returns:
            List of batches
        """
        batches = []
        for i in range(0, len(sections), batch_size):
            batches.append(sections[i:i + batch_size])
        return batches

    @staticmethod
    def by_priority(sections: List[Section], priorities: Dict[str, int]) -> List[List[Section]]:
        """
        Batch sections by priority level.

        Args:
            sections: List of sections
            priorities: Dictionary mapping section_id to priority

        Returns:
            List of batches sorted by priority
        """
        priority_map: Dict[int, List[Section]] = {}

        for section in sections:
            priority = priorities.get(section.id, 0)
            if priority not in priority_map:
                priority_map[priority] = []
            priority_map[priority].append(section)

        # Return batches sorted by priority (highest first)
        return [priority_map[p] for p in sorted(priority_map.keys(), reverse=True)]


def estimate_speedup(num_sections: int, max_workers: int = 3) -> Dict[str, Any]:
    """
    Estimate speedup from parallel drafting.

    Args:
        num_sections: Number of sections to draft
        max_workers: Number of parallel workers

    Returns:
        Dictionary with speedup estimates
    """
    # Assume average 60 seconds per section
    avg_section_time = 60.0

    # Sequential time
    sequential_time = num_sections * avg_section_time

    # Parallel time (with some overhead)
    parallel_batches = (num_sections + max_workers - 1) // max_workers
    parallel_time = parallel_batches * avg_section_time * 1.1  # 10% overhead

    speedup = sequential_time / parallel_time if parallel_time > 0 else 1.0

    return {
        "num_sections": num_sections,
        "max_workers": max_workers,
        "sequential_time_seconds": sequential_time,
        "parallel_time_seconds": parallel_time,
        "speedup": speedup,
        "time_saved_seconds": sequential_time - parallel_time,
        "time_saved_minutes": (sequential_time - parallel_time) / 60
    }
