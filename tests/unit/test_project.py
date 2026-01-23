"""Unit tests for project management."""

import pytest
from pathlib import Path
import json
from datetime import datetime

from papergen.core.project import PaperProject
from papergen.core.state import ProjectState, ProjectMetadata
from papergen.core.exceptions import (
    ProjectNotFoundError,
    ProjectAlreadyExistsError,
    ProjectStateError
)


class TestProjectInitialization:
    """Test project initialization."""

    def test_initialize_new_project(self, temp_dir):
        """Test initializing a new project."""
        project = PaperProject(temp_dir)
        state = project.initialize(
            topic="Test Paper",
            template="ieee",
            format="latex"
        )

        assert state.topic == "Test Paper"
        assert state.template == "ieee"
        assert state.format == "latex"
        assert (temp_dir / ".papergen").exists()
        assert (temp_dir / ".papergen" / "state.json").exists()

    def test_initialize_creates_directory_structure(self, temp_dir):
        """Test that initialization creates all required directories."""
        project = PaperProject(temp_dir)
        project.initialize(topic="Test Paper")

        # Check all directories exist
        assert (temp_dir / ".papergen").exists()
        assert (temp_dir / ".papergen" / "cache").exists()
        assert (temp_dir / "sources" / "pdfs").exists()
        assert (temp_dir / "sources" / "notes").exists()
        assert (temp_dir / "sources" / "extracted").exists()
        assert (temp_dir / "research").exists()
        assert (temp_dir / "outline").exists()
        assert (temp_dir / "drafts" / "versions").exists()
        assert (temp_dir / "revisions").exists()
        assert (temp_dir / "output" / "figures").exists()

    def test_initialize_with_metadata(self, temp_dir):
        """Test initializing with custom metadata."""
        project = PaperProject(temp_dir)
        metadata = {
            "title": "Custom Title",
            "authors": ["Author One", "Author Two"],
            "abstract": "Custom abstract"
        }
        state = project.initialize(
            topic="Test Paper",
            metadata=metadata
        )

        assert state.metadata.title == "Custom Title"
        assert state.metadata.authors == ["Author One", "Author Two"]
        assert state.metadata.abstract == "Custom abstract"

    def test_initialize_existing_project_raises_error(self, sample_project):
        """Test that initializing an existing project raises error."""
        with pytest.raises(ProjectAlreadyExistsError) as exc_info:
            sample_project.initialize(topic="Another Paper")

        assert str(sample_project.root_path) in str(exc_info.value)

    def test_initialize_creates_config_file(self, temp_dir):
        """Test that initialization creates project config file."""
        project = PaperProject(temp_dir)
        project.initialize(topic="Test Paper", template="acm")

        config_file = temp_dir / ".papergen" / "config.yaml"
        assert config_file.exists()

        # Check config content
        with open(config_file) as f:
            content = f.read()
            assert "template: acm" in content
            assert "word_counts:" in content


class TestProjectStateManagement:
    """Test project state loading and saving."""

    def test_load_state(self, sample_project):
        """Test loading project state."""
        state = sample_project.load_state()

        assert state.topic == "Test Paper on Machine Learning"
        assert state.template == "ieee"
        assert state.format == "latex"

    def test_load_state_nonexistent_project(self, temp_dir):
        """Test loading state from nonexistent project."""
        project = PaperProject(temp_dir)

        with pytest.raises(ProjectNotFoundError) as exc_info:
            project.load_state()

        assert str(temp_dir) in str(exc_info.value)

    def test_save_state(self, sample_project):
        """Test saving project state."""
        state = sample_project.state
        state.topic = "Updated Topic"

        sample_project.save_state()

        # Reload and verify
        reloaded_state = sample_project.load_state()
        assert reloaded_state.topic == "Updated Topic"

    def test_save_state_without_loading_raises_error(self, temp_dir):
        """Test saving state without loading first raises error."""
        project = PaperProject(temp_dir)
        project.initialize(topic="Test")

        # Create new project instance without loading
        new_project = PaperProject(temp_dir)

        with pytest.raises(ProjectStateError):
            new_project.save_state()

    def test_state_property_lazy_loads(self, sample_project):
        """Test that state property lazy loads state."""
        # Create new project instance
        project = PaperProject(sample_project.root_path)

        # Access state property (should load automatically)
        state = project.state

        assert state.topic == "Test Paper on Machine Learning"

    def test_update_state(self, sample_project):
        """Test updating state fields."""
        sample_project.update_state(topic="New Topic")

        state = sample_project.load_state()
        assert state.topic == "New Topic"
        assert state.updated_at is not None


class TestProjectPaths:
    """Test project path methods."""

    def test_config_dir_path(self, sample_project):
        """Test config directory path."""
        assert sample_project.config_dir == sample_project.root_path / ".papergen"

    def test_state_file_path(self, sample_project):
        """Test state file path."""
        assert sample_project.state_file == sample_project.root_path / ".papergen" / "state.json"


class TestProjectStateCorruption:
    """Test handling of corrupted project state."""

    def test_load_corrupted_state_file(self, temp_dir):
        """Test loading a corrupted state file."""
        project = PaperProject(temp_dir)
        project.initialize(topic="Test")

        # Corrupt the state file
        with open(project.state_file, 'w') as f:
            f.write("{ invalid json }")

        with pytest.raises(ProjectStateError) as exc_info:
            project.load_state()

        assert "Failed to load state file" in str(exc_info.value)
