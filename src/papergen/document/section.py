"""Section management and drafting."""

from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from ..document.outline import Section
from ..document.citation import CitationManager


class SectionDraft:
    """Represents a drafted section with metadata."""

    def __init__(
        self,
        section_id: str,
        content: str,
        version: int = 1,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.section_id = section_id
        self.content = content
        self.version = version
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.metadata = metadata or {}
        self.word_count = len(content.split())
        self.citation_keys = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "section_id": self.section_id,
            "content": self.content,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
            "word_count": self.word_count,
            "citation_keys": self.citation_keys
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SectionDraft':
        """Create from dictionary."""
        draft = cls(
            section_id=data['section_id'],
            content=data['content'],
            version=data.get('version', 1),
            metadata=data.get('metadata', {})
        )
        if 'created_at' in data:
            draft.created_at = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data:
            draft.updated_at = datetime.fromisoformat(data['updated_at'])
        draft.word_count = data.get('word_count', len(draft.content.split()))
        draft.citation_keys = data.get('citation_keys', [])
        return draft


class SectionManager:
    """Manages section drafting and revisions."""

    def __init__(
        self,
        project_root: Path,
        claude_client=None,
        citation_manager: Optional[CitationManager] = None
    ):
        """
        Initialize section manager.

        Args:
            project_root: Project root directory
            claude_client: Claude API client
            citation_manager: Citation manager instance
        """
        self.project_root = Path(project_root)
        self.drafts_dir = self.project_root / "drafts"
        self.versions_dir = self.drafts_dir / "versions"
        self.claude_client = claude_client
        self.citation_manager = citation_manager or CitationManager()

        # Ensure directories exist
        self.drafts_dir.mkdir(parents=True, exist_ok=True)
        self.versions_dir.mkdir(parents=True, exist_ok=True)

    def draft_section(
        self,
        section: Section,
        research_text: str,
        guidance: str = ""
    ) -> SectionDraft:
        """
        Draft a section using AI.

        Args:
            section: Section outline
            research_text: Relevant research text
            guidance: Optional additional guidance

        Returns:
            SectionDraft object
        """
        if not self.claude_client:
            raise ValueError("Claude client required for drafting")

        from ..ai.prompts import PromptLibrary

        # Generate prompt
        system_prompt, user_prompt = PromptLibrary.section_drafting(
            section_title=section.title,
            objectives=section.objectives,
            key_points=section.key_points,
            research=research_text,
            guidance=guidance or section.guidance or "",
            word_count_target=section.word_count_target
        )

        # Call Claude
        content = self.claude_client.generate(
            prompt=user_prompt,
            system=system_prompt,
            max_tokens=8000,
            temperature=0.7
        )

        # Create draft
        draft = SectionDraft(
            section_id=section.id,
            content=content,
            version=1,
            metadata={
                "section_title": section.title,
                "word_count_target": section.word_count_target,
                "generated_with": "claude",
                "ai_model": getattr(self.claude_client, 'model', 'unknown')
            }
        )

        # Extract citation keys
        draft.citation_keys = self.citation_manager.extract_citations_from_text(content)

        return draft

    def save_draft(self, draft: SectionDraft) -> Path:
        """
        Save draft to file.

        Args:
            draft: SectionDraft to save

        Returns:
            Path to saved file
        """
        # Save main draft file
        draft_file = self.drafts_dir / f"{draft.section_id}.md"
        with open(draft_file, 'w') as f:
            f.write(draft.content)

        # Save metadata
        metadata_file = self.drafts_dir / f"{draft.section_id}.json"
        with open(metadata_file, 'w') as f:
            json.dump(draft.to_dict(), f, indent=2, default=str)

        # Save version
        version_file = self.versions_dir / f"{draft.section_id}_v{draft.version}.md"
        with open(version_file, 'w') as f:
            f.write(draft.content)

        return draft_file

    def load_draft(self, section_id: str) -> Optional[SectionDraft]:
        """
        Load draft from file.

        Args:
            section_id: Section ID

        Returns:
            SectionDraft or None if not found
        """
        metadata_file = self.drafts_dir / f"{section_id}.json"
        if not metadata_file.exists():
            return None

        with open(metadata_file, 'r') as f:
            data = json.load(f)

        return SectionDraft.from_dict(data)

    def get_draft_content(self, section_id: str) -> Optional[str]:
        """Get draft content as string."""
        draft_file = self.drafts_dir / f"{section_id}.md"
        if not draft_file.exists():
            return None

        with open(draft_file, 'r') as f:
            return f.read()

    def list_drafts(self) -> List[str]:
        """List all drafted section IDs."""
        draft_files = self.drafts_dir.glob("*.md")
        return [f.stem for f in draft_files if f.name != "versions"]

    def get_version_history(self, section_id: str) -> List[int]:
        """Get list of version numbers for a section."""
        version_files = self.versions_dir.glob(f"{section_id}_v*.md")
        versions = []
        for f in version_files:
            try:
                version = int(f.stem.split('_v')[1])
                versions.append(version)
            except (IndexError, ValueError):
                continue
        return sorted(versions)

    def review_section(self, section_id: str) -> str:
        """
        Get AI review of a drafted section.

        Args:
            section_id: Section ID to review

        Returns:
            Review text
        """
        if not self.claude_client:
            raise ValueError("Claude client required for review")

        draft = self.load_draft(section_id)
        if not draft:
            raise ValueError(f"No draft found for section: {section_id}")

        from ..ai.prompts import PromptLibrary

        system_prompt, user_prompt = PromptLibrary.section_review(
            section_title=draft.metadata.get('section_title', section_id),
            content=draft.content
        )

        review = self.claude_client.generate(
            prompt=user_prompt,
            system=system_prompt,
            max_tokens=2048,
            temperature=0.7
        )

        return review

    def update_draft(
        self,
        section_id: str,
        new_content: str,
        increment_version: bool = True
    ) -> SectionDraft:
        """
        Update an existing draft.

        Args:
            section_id: Section ID
            new_content: New content
            increment_version: Whether to increment version number

        Returns:
            Updated SectionDraft
        """
        # Load existing draft
        existing = self.load_draft(section_id)

        if existing and increment_version:
            version = existing.version + 1
            metadata = existing.metadata
        else:
            version = 1
            metadata = {}

        # Create new draft
        draft = SectionDraft(
            section_id=section_id,
            content=new_content,
            version=version,
            metadata=metadata
        )

        draft.updated_at = datetime.now()
        draft.citation_keys = self.citation_manager.extract_citations_from_text(new_content)

        # Save
        self.save_draft(draft)

        return draft

    def get_statistics(self) -> Dict[str, Any]:
        """Get drafting statistics."""
        drafts = self.list_drafts()

        total_words = 0
        total_citations = 0

        for section_id in drafts:
            draft = self.load_draft(section_id)
            if draft:
                total_words += draft.word_count
                total_citations += len(draft.citation_keys)

        return {
            "sections_drafted": len(drafts),
            "total_words": total_words,
            "total_citations": total_citations,
            "average_words_per_section": total_words // len(drafts) if drafts else 0
        }
