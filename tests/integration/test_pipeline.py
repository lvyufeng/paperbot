"""Integration tests for the paper generation pipeline."""

import pytest
from pathlib import Path
import json

from papergen.core.project import PaperProject
from papergen.sources.pdf_extractor import PDFExtractor
from papergen.sources.text_extractor import TextExtractor


@pytest.mark.integration
class TestPaperGenerationPipeline:
    """Test the complete paper generation pipeline."""

    def test_full_pipeline_initialization(self, temp_dir):
        """Test initializing a project and verifying structure."""
        project = PaperProject(temp_dir)
        state = project.initialize(
            topic="Integration Test Paper",
            template="ieee",
            format="latex",
            metadata={
                "title": "Integration Test",
                "authors": ["Test Author"]
            }
        )

        # Verify project structure
        assert state.topic == "Integration Test Paper"
        assert (temp_dir / ".papergen").exists()
        assert (temp_dir / "sources").exists()
        assert (temp_dir / "drafts").exists()

        # Verify state persistence
        reloaded_project = PaperProject(temp_dir)
        reloaded_state = reloaded_project.load_state()
        assert reloaded_state.topic == state.topic
        assert reloaded_state.project_id == state.project_id

    def test_add_text_source_to_project(self, sample_project, temp_dir, sample_text_content):
        """Test adding a text source to the project."""
        # Create a text file
        text_file = temp_dir / "source.txt"
        text_file.write_text(sample_text_content)

        # Extract content
        extractor = TextExtractor()
        extracted = extractor.extract(text_file)

        # Verify extraction
        assert "content" in extracted
        assert len(extracted["content"]["full_text"]) > 100

    def test_project_state_updates(self, sample_project):
        """Test updating project state through the pipeline."""
        original_topic = sample_project.state.topic

        # Update state
        sample_project.update_state(topic="Updated Topic")

        # Verify update persisted
        new_project = PaperProject(sample_project.root_path)
        assert new_project.state.topic == "Updated Topic"
        assert new_project.state.topic != original_topic


@pytest.mark.integration
class TestSourceManagement:
    """Test source management integration."""

    def test_add_multiple_sources(self, sample_project, temp_dir, sample_text_content):
        """Test adding multiple sources to a project."""
        sources_dir = temp_dir / "sources" / "extracted"
        sources_dir.mkdir(parents=True, exist_ok=True)

        # Create multiple text sources
        for i in range(3):
            text_file = temp_dir / f"source_{i}.txt"
            text_file.write_text(sample_text_content)

            extractor = TextExtractor()
            extracted = extractor.extract(text_file)

            # Save extracted content
            extracted_file = sources_dir / f"source_{i}.json"
            with open(extracted_file, 'w') as f:
                json.dump(extracted, f, indent=2, default=str)

        # Verify all sources were saved
        extracted_files = list(sources_dir.glob("*.json"))
        assert len(extracted_files) == 3


@pytest.mark.integration
@pytest.mark.slow
class TestEndToEndWorkflow:
    """Test end-to-end workflow scenarios."""

    def test_create_project_and_add_source(self, temp_dir, sample_text_content):
        """Test creating a project and adding a source."""
        # Step 1: Initialize project
        project = PaperProject(temp_dir)
        project.initialize(
            topic="End-to-End Test Paper",
            template="ieee"
        )

        # Step 2: Create and add a source
        text_file = temp_dir / "research_paper.txt"
        text_file.write_text(sample_text_content)

        extractor = TextExtractor()
        extracted = extractor.extract(text_file)

        # Step 3: Save extracted content
        extracted_dir = temp_dir / "sources" / "extracted"
        extracted_dir.mkdir(parents=True, exist_ok=True)

        extracted_file = extracted_dir / "source_001.json"
        with open(extracted_file, 'w') as f:
            json.dump(extracted, f, indent=2, default=str)

        # Step 4: Verify everything is in place
        assert project.state_file.exists()
        assert extracted_file.exists()

        # Step 5: Reload project and verify
        new_project = PaperProject(temp_dir)
        state = new_project.load_state()
        assert state.topic == "End-to-End Test Paper"


@pytest.mark.integration
class TestErrorRecovery:
    """Test error recovery in the pipeline."""

    def test_recover_from_corrupted_state(self, sample_project):
        """Test handling of corrupted state file."""
        from papergen.core.exceptions import ProjectStateError

        # Corrupt the state file
        with open(sample_project.state_file, 'w') as f:
            f.write("{ invalid json }")

        # Try to load - should raise ProjectStateError
        new_project = PaperProject(sample_project.root_path)
        with pytest.raises(ProjectStateError):
            new_project.load_state()

    def test_handle_missing_directories(self, temp_dir):
        """Test handling of missing project directories."""
        from papergen.core.exceptions import ProjectNotFoundError

        project = PaperProject(temp_dir)

        # Try to load state without initializing
        with pytest.raises(ProjectNotFoundError):
            project.load_state()
