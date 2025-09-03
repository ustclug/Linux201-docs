"""
Shared pytest fixtures and configuration.

This file contains common fixtures that can be used across all tests
in the test suite. Fixtures defined here are automatically available
to all test files without needing to import them.
"""

import os
import tempfile
from pathlib import Path
from typing import Generator, Dict, Any
import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """
    Create a temporary directory for testing.
    
    Yields:
        Path: Path to the temporary directory
        
    The directory and its contents are automatically cleaned up after the test.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def temp_file(temp_dir: Path) -> Generator[Path, None, None]:
    """
    Create a temporary file for testing.
    
    Args:
        temp_dir: Temporary directory fixture
        
    Yields:
        Path: Path to the temporary file
    """
    temp_file = temp_dir / "test_file.txt"
    temp_file.write_text("test content")
    yield temp_file


@pytest.fixture
def mock_config() -> Dict[str, Any]:
    """
    Provide a mock configuration dictionary for testing.
    
    Returns:
        Dict[str, Any]: Mock configuration data
    """
    return {
        "debug": True,
        "log_level": "INFO",
        "timeout": 30,
        "retry_attempts": 3,
        "test_mode": True
    }


@pytest.fixture
def sample_markdown_content() -> str:
    """
    Provide sample markdown content for testing documentation-related functionality.
    
    Returns:
        str: Sample markdown content
    """
    return """# Test Document

This is a test document with various markdown elements.

## Section 1

Some content here with **bold** and *italic* text.

### Subsection 1.1

- Item 1
- Item 2
- Item 3

```python
def hello_world():
    print("Hello, World!")
```

## Section 2

More content here.
"""


@pytest.fixture
def mock_environment_vars() -> Generator[None, None, None]:
    """
    Set up mock environment variables for testing.
    
    This fixture sets test-specific environment variables and ensures
    they are cleaned up after the test completes.
    """
    original_env = os.environ.copy()
    
    # Set test environment variables
    test_env_vars = {
        "TEST_MODE": "true",
        "LOG_LEVEL": "DEBUG",
        "CONFIG_PATH": "/tmp/test_config",
    }
    
    os.environ.update(test_env_vars)
    
    try:
        yield
    finally:
        # Restore original environment
        os.environ.clear()
        os.environ.update(original_env)


@pytest.fixture
def capture_logs(caplog):
    """
    Fixture to capture and analyze log output during tests.
    
    Args:
        caplog: pytest's built-in log capture fixture
        
    Returns:
        The caplog fixture for log analysis
    """
    with caplog.at_level("DEBUG"):
        yield caplog


@pytest.fixture(autouse=True)
def clean_test_artifacts():
    """
    Auto-use fixture to clean up test artifacts after each test.
    
    This fixture runs after every test to ensure no temporary files
    or other test artifacts are left behind.
    """
    yield
    
    # Clean up any test artifacts
    test_files = [
        "test_output.txt",
        "test_config.json",
        ".test_cache"
    ]
    
    for file_name in test_files:
        file_path = Path(file_name)
        if file_path.exists():
            if file_path.is_file():
                file_path.unlink()
            elif file_path.is_dir():
                import shutil
                shutil.rmtree(file_path)