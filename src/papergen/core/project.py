"""Project workspace management for PaperGen."""

from datetime import datetime
from pathlib import Path
from typing import Optional
import uuid

from ..core.state import ProjectState, ProjectMetadata
from ..core.config import Config


class PaperProject:
    """Manages a paper project workspace."""

    def __init__(self, root_path: Path):
        """
        Initialize project manager.

        Args:
            root_path: Root directory of the project
        """
        self.root_path = Path(root_path)
        self.config_dir = self.root_path / ".papergen"
        self.state_file = self.config_dir / "state.json"
        self._state: Optional[ProjectState] = None

    def initialize(
        self,
        topic: str,
        template: str = "ieee",
        format: str = "latex",
        metadata: Optional[dict] = None
    ) -> ProjectState:
        """
        Initialize a new project workspace.

        Args:
            topic: Research topic/title
            template: Template to use (ieee, acm, springer)
            format: Output format (latex, markdown)
            metadata: Optional project metadata

        Returns:
            Initialized ProjectState
        """
        # Create directory structure
        directories = [
            self.config_dir,
            self.config_dir / "cache",
            self.root_path / "sources" / "pdfs",
            self.root_path / "sources" / "notes",
            self.root_path / "sources" / "extracted",
            self.root_path / "research",
            self.root_path / "outline",
            self.root_path / "drafts" / "versions",
            self.root_path / "revisions",
            self.root_path / "output" / "figures",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

        # Create .gitkeep files for empty directories
        for directory in directories:
            gitkeep = directory / ".gitkeep"
            if not any(directory.iterdir()):  # Only if empty
                gitkeep.touch()

        # Initialize state
        project_metadata = ProjectMetadata(**(metadata or {}))
        if not project_metadata.title:
            project_metadata.title = topic

        state = ProjectState(
            project_id=str(uuid.uuid4()),
            topic=topic,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            template=template,
            format=format,
            metadata=project_metadata
        )

        # Save state
        state.save(self.state_file)
        self._state = state

        # Create project config
        config_file = self.config_dir / "config.yaml"
        self._create_project_config(config_file, template, format)

        return state

    def _create_project_config(self, config_file: Path, template: str, format: str) -> None:
        """Create project-specific configuration."""
        config_content = f"""# PaperGen Project Configuration

# Paper settings
template: {template}
format: {format}

# Section word count targets
word_counts:
  abstract: 250
  introduction: 1500
  related_work: 1000
  methods: 1500
  results: 1500
  discussion: 1000
  conclusion: 500

# Citation settings
citation_style: apa

# AI settings (inherits from global config)
# Uncomment to override
# ai:
#   model: claude-opus-4-5
#   temperature: 0.7
#   max_tokens: 4096
"""
        with open(config_file, 'w') as f:
            f.write(config_content)

    def load_state(self) -> ProjectState:
        """
        Load project state from disk.

        Returns:
            ProjectState object

        Raises:
            FileNotFoundError: If state file doesn't exist
        """
        if not self.state_file.exists():
            raise FileNotFoundError(
                f"Project state not found. Run 'papergen init' first.\n"
                f"Looking for: {self.state_file}"
            )

        self._state = ProjectState.load(self.state_file)
        return self._state

    def save_state(self) -> None:
        """Save current state to disk."""
        if self._state is None:
            raise ValueError("No state to save. Load or initialize state first.")
        self._state.save(self.state_file)

    @property
    def state(self) -> ProjectState:
        """Get current project state."""
        if self._state is None:
            self._state = self.load_state()
        return self._state

    def update_state(self, **kwargs) -> None:
        """Update state fields and save."""
        state = self.state
        for key, value in kwargs.items():
            if hasattr(state, key):
                setattr(state, key, value)
        state.updated_at = datetime.now()
        self.save_state()

    def validate_structure(self) -> bool:
        """
        Validate that project structure is intact.

        Returns:
            True if valid, False otherwise
        """
        required_dirs = [
            self.config_dir,
            self.root_path / "sources",
            self.root_path / "research",
            self.root_path / "outline",
            self.root_path / "drafts",
            self.root_path / "output",
        ]

        for directory in required_dirs:
            if not directory.exists():
                return False

        if not self.state_file.exists():
            return False

        return True

    def get_sources_dir(self) -> Path:
        """Get sources directory."""
        return self.root_path / "sources"

    def get_extracted_dir(self) -> Path:
        """Get extracted sources directory."""
        return self.root_path / "sources" / "extracted"

    def get_research_dir(self) -> Path:
        """Get research directory."""
        return self.root_path / "research"

    def get_outline_dir(self) -> Path:
        """Get outline directory."""
        return self.root_path / "outline"

    def get_drafts_dir(self) -> Path:
        """Get drafts directory."""
        return self.root_path / "drafts"

    def get_output_dir(self) -> Path:
        """Get output directory."""
        return self.root_path / "output"

    def has_research(self) -> bool:
        """Check if project has research sources."""
        extracted_dir = self.get_extracted_dir()
        return any(extracted_dir.glob("*.json"))

    def has_outline(self) -> bool:
        """Check if project has an outline."""
        outline_file = self.get_outline_dir() / "outline.json"
        return outline_file.exists()

    @classmethod
    def find_project_root(cls, start_path: Optional[Path] = None) -> Optional[Path]:
        """
        Find project root by looking for .papergen directory.

        Args:
            start_path: Starting path to search from (default: current directory)

        Returns:
            Path to project root or None if not found
        """
        current = Path(start_path or Path.cwd()).resolve()

        # Search up to 10 levels
        for _ in range(10):
            if (current / ".papergen").exists():
                return current
            if current.parent == current:  # Reached filesystem root
                break
            current = current.parent

        return None
