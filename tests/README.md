# PaperGen Test Suite

Comprehensive test suite for PaperGen with unit tests, integration tests, and fixtures.

## Test Structure

```
tests/
├── conftest.py              # Pytest configuration and shared fixtures
├── unit/                    # Unit tests (fast, isolated)
│   ├── test_exceptions.py   # Exception hierarchy tests
│   ├── test_project.py      # Project management tests
│   ├── test_pdf_extractor.py # PDF extraction tests
│   └── test_web_extractor.py # Web extraction tests
├── integration/             # Integration tests (slower, end-to-end)
│   └── test_pipeline.py     # Full pipeline tests
└── fixtures/                # Test fixtures (sample files)
    └── sample_paper.pdf     # Sample PDF for testing

```

## Running Tests

### Run All Tests
```bash
pytest
```

### Run Unit Tests Only
```bash
pytest tests/unit/
```

### Run Integration Tests Only
```bash
pytest tests/integration/
```

### Run with Coverage
```bash
pytest --cov=src/papergen --cov-report=html
```

### Run Specific Test File
```bash
pytest tests/unit/test_exceptions.py
```

### Run Specific Test
```bash
pytest tests/unit/test_exceptions.py::TestExceptionHierarchy::test_base_exception
```

### Run Tests by Marker
```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"

# Skip tests requiring API
pytest -m "not requires_api"
```

### Verbose Output
```bash
pytest -v
```

### Show Print Statements
```bash
pytest -s
```

## Test Markers

Tests are marked with the following markers:

- `@pytest.mark.unit` - Fast, isolated unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow running tests
- `@pytest.mark.requires_api` - Tests requiring API access

## Fixtures

### Common Fixtures (conftest.py)

- `temp_dir` - Temporary directory for tests
- `sample_project` - Initialized PaperGen project
- `sample_pdf_path` - Path to sample PDF file
- `sample_text_content` - Sample text content
- `sample_extracted_content` - Sample extracted content structure
- `mock_claude_response` - Mock Claude API response
- `mock_api_key` - Mock API key
- `sample_config` - Sample configuration
- `sample_project_state` - Sample project state
- `sample_sources` - Sample research sources
- `sample_outline` - Sample paper outline

## Writing Tests

### Unit Test Example

```python
import pytest
from papergen.core.exceptions import PDFExtractionError

def test_pdf_extraction_error():
    """Test PDFExtractionError."""
    exc = PDFExtractionError("test.pdf", "File corrupted")

    assert exc.file_path == "test.pdf"
    assert exc.reason == "File corrupted"
    assert "test.pdf" in str(exc)
```

### Integration Test Example

```python
@pytest.mark.integration
def test_full_pipeline(sample_project, temp_dir):
    """Test complete pipeline."""
    # Test implementation
    pass
```

### Using Fixtures

```python
def test_with_temp_dir(temp_dir):
    """Test using temporary directory."""
    test_file = temp_dir / "test.txt"
    test_file.write_text("content")
    assert test_file.exists()
```

### Mocking API Calls

```python
from unittest.mock import patch

@patch('papergen.ai.claude_client.anthropic.Anthropic')
def test_api_call(mock_anthropic):
    """Test API call with mocking."""
    mock_anthropic.return_value.messages.create.return_value = Mock(
        content=[Mock(text="response")]
    )
    # Test implementation
```

## Coverage

Coverage reports are generated in `htmlcov/` directory.

View coverage report:
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

## Test Guidelines

### Unit Tests
- Test single units of code in isolation
- Mock external dependencies
- Fast execution (< 1 second per test)
- No file I/O or network calls
- Use descriptive test names

### Integration Tests
- Test multiple components together
- May use real file I/O
- Can be slower
- Test realistic scenarios
- Mark with `@pytest.mark.integration`

### Best Practices
1. **One assertion per test** (when possible)
2. **Arrange-Act-Assert** pattern
3. **Descriptive test names** that explain what is being tested
4. **Use fixtures** for common setup
5. **Mock external dependencies** (APIs, file system)
6. **Test edge cases** and error conditions
7. **Keep tests independent** - no test should depend on another

### Example Test Structure

```python
def test_feature_name():
    """Test description explaining what is being tested."""
    # Arrange - Set up test data
    extractor = PDFExtractor()
    test_file = Path("test.pdf")

    # Act - Execute the code being tested
    result = extractor.extract(test_file)

    # Assert - Verify the results
    assert result is not None
    assert "content" in result
```

## Continuous Integration

Tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pip install -e ".[dev]"
    pytest --cov=src/papergen --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Test Data

### Sample PDF
Place a sample PDF file in `tests/fixtures/sample_paper.pdf` for PDF extraction tests.

### Sample Text
Sample text content is provided in fixtures for testing text extraction.

## Troubleshooting

### Tests Fail with Import Errors
```bash
# Install package in development mode
pip install -e .
pip install -e ".[dev]"
```

### Coverage Not Working
```bash
# Install coverage dependencies
pip install pytest-cov
```

### Slow Tests
```bash
# Skip slow tests
pytest -m "not slow"
```

## Current Test Coverage

### Implemented Tests
- ✅ Exception hierarchy (30+ tests)
- ✅ Project management (15+ tests)
- ✅ PDF extraction (10+ tests)
- ✅ Web extraction (10+ tests)
- ✅ Integration pipeline (5+ tests)

### TODO: Additional Tests Needed
- [ ] Claude client tests
- [ ] OpenAI client tests
- [ ] Configuration tests
- [ ] State management tests
- [ ] Outline generation tests
- [ ] Draft generation tests
- [ ] Revision tests
- [ ] Formatting tests
- [ ] Citation management tests
- [ ] Semantic Scholar integration tests

## Contributing

When adding new features:
1. Write tests first (TDD)
2. Ensure tests pass
3. Maintain >80% coverage
4. Add integration tests for new workflows
5. Update this README if adding new test categories

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [Pytest Markers](https://docs.pytest.org/en/stable/mark.html)
- [Coverage.py](https://coverage.readthedocs.io/)
