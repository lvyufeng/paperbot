"""Core state management for PaperGen pipeline."""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
import json

from pydantic import BaseModel, Field


class StageStatus(str, Enum):
    """Status of a pipeline stage."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class SourceType(str, Enum):
    """Type of research source."""
    PDF = "pdf"
    WEB = "web"
    TEXT = "text"
    NOTE = "note"


class Source(BaseModel):
    """Represents a research source."""
    id: str
    type: SourceType
    original_path: str
    extracted_path: str
    added_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
    extraction_status: str = "pending"
    relevance_score: Optional[float] = None


class Section(BaseModel):
    """Represents a paper section in the outline."""
    id: str
    title: str
    level: int  # 0=abstract, 1=main, 2=subsection
    order: int
    objectives: List[str] = Field(default_factory=list)
    key_points: List[str] = Field(default_factory=list)
    word_count_target: int = 500
    sources: List[str] = Field(default_factory=list)  # Source IDs
    guidance: Optional[str] = None
    subsections: List['Section'] = Field(default_factory=list)


# Enable forward references
Section.model_rebuild()


class Draft(BaseModel):
    """Represents a section draft."""
    section_id: str
    version: int
    created_at: datetime
    updated_at: datetime
    status: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    revision_history: List[Dict[str, Any]] = Field(default_factory=list)


class ProjectMetadata(BaseModel):
    """Paper metadata."""
    title: Optional[str] = None
    authors: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    abstract: Optional[str] = None
    conference: Optional[str] = None
    institution: Optional[str] = None


class StageInfo(BaseModel):
    """Information about a pipeline stage."""
    status: StageStatus = StageStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProjectState(BaseModel):
    """Central state for paper project."""
    version: str = "1.0"
    project_id: str
    topic: str
    created_at: datetime
    updated_at: datetime
    current_stage: str = "research"
    template: str = "ieee"
    format: str = "latex"  # latex or markdown
    metadata: ProjectMetadata = Field(default_factory=ProjectMetadata)
    stages: Dict[str, StageInfo] = Field(default_factory=dict)

    def __init__(self, **data: Any):
        super().__init__(**data)
        # Initialize stages if not present
        if not self.stages:
            for stage in ["research", "outline", "draft", "revise", "format"]:
                self.stages[stage] = StageInfo()

    def can_proceed_to(self, stage: str) -> bool:
        """Check if dependencies are met for stage."""
        stage_order = ["research", "outline", "draft", "revise", "format"]

        if stage not in stage_order:
            return False

        current_idx = stage_order.index(self.current_stage)
        target_idx = stage_order.index(stage)

        # Can only proceed to next stage or stay at current
        if target_idx > current_idx + 1:
            return False

        # Check that previous stages are completed
        for i in range(target_idx):
            stage_name = stage_order[i]
            if self.stages[stage_name].status != StageStatus.COMPLETED:
                return False

        return True

    def mark_stage_started(self, stage: str) -> None:
        """Mark a stage as started."""
        if stage not in self.stages:
            self.stages[stage] = StageInfo()
        self.stages[stage].status = StageStatus.IN_PROGRESS
        self.stages[stage].started_at = datetime.now()
        self.current_stage = stage
        self.updated_at = datetime.now()

    def mark_stage_completed(self, stage: str) -> None:
        """Mark a stage as completed."""
        if stage not in self.stages:
            self.stages[stage] = StageInfo()
        self.stages[stage].status = StageStatus.COMPLETED
        self.stages[stage].completed_at = datetime.now()
        self.updated_at = datetime.now()

    def mark_stage_failed(self, stage: str, error: str) -> None:
        """Mark a stage as failed."""
        if stage not in self.stages:
            self.stages[stage] = StageInfo()
        self.stages[stage].status = StageStatus.FAILED
        self.stages[stage].metadata["error"] = error
        self.updated_at = datetime.now()

    def save(self, path: Path) -> None:
        """Save state to JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.model_dump(mode='json'), f, indent=2, default=str)

    @classmethod
    def load(cls, path: Path) -> 'ProjectState':
        """Load state from JSON file."""
        with open(path, 'r') as f:
            data = json.load(f)
        return cls(**data)

    def get_stage_status(self, stage: str) -> StageStatus:
        """Get status of a stage."""
        if stage in self.stages:
            return self.stages[stage].status
        return StageStatus.PENDING
