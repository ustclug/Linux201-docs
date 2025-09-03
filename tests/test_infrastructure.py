"""
Validation tests to ensure the testing infrastructure is properly set up.

These tests verify that the testing environment is correctly configured
and that all components are working as expected.
"""

import os
import sys
from pathlib import Path
import pytest


class TestInfrastructure:
    """Test class to validate testing infrastructure setup."""
    
    def test_python_version(self):
        """Test that Python version is compatible."""
        assert sys.version_info >= (3, 8), "Python 3.8 or higher is required"
    
    def test_pytest_import(self):
        """Test that pytest can be imported."""
        import pytest
        assert pytest is not None
    
    def test_pytest_cov_import(self):
        """Test that pytest-cov can be imported."""
        import pytest_cov
        assert pytest_cov is not None
    
    def test_pytest_mock_import(self):
        """Test that pytest-mock can be imported."""
        import pytest_mock
        assert pytest_mock is not None
    
    @pytest.mark.unit
    def test_unit_marker(self):
        """Test that unit marker is properly configured."""
        assert True
    
    @pytest.mark.integration
    def test_integration_marker(self):
        """Test that integration marker is properly configured."""
        assert True
    
    @pytest.mark.slow
    def test_slow_marker(self):
        """Test that slow marker is properly configured."""
        assert True
    
    def test_temp_dir_fixture(self, temp_dir):
        """Test that temp_dir fixture works correctly."""
        assert temp_dir.exists()
        assert temp_dir.is_dir()
        
        # Create a test file in the temp directory
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        assert test_file.exists()
        assert test_file.read_text() == "test content"
    
    def test_temp_file_fixture(self, temp_file):
        """Test that temp_file fixture works correctly."""
        assert temp_file.exists()
        assert temp_file.is_file()
        assert temp_file.read_text() == "test content"
    
    def test_mock_config_fixture(self, mock_config):
        """Test that mock_config fixture provides expected data."""
        assert isinstance(mock_config, dict)
        assert "debug" in mock_config
        assert "log_level" in mock_config
        assert "timeout" in mock_config
        assert mock_config["test_mode"] is True
    
    def test_sample_markdown_content_fixture(self, sample_markdown_content):
        """Test that sample_markdown_content fixture provides markdown."""
        assert isinstance(sample_markdown_content, str)
        assert "# Test Document" in sample_markdown_content
        assert "```python" in sample_markdown_content
    
    def test_mock_environment_vars(self, mock_environment_vars):
        """Test that environment variables fixture works."""
        assert os.environ.get("TEST_MODE") == "true"
        assert os.environ.get("LOG_LEVEL") == "DEBUG"
    
    def test_project_structure(self):
        """Test that project has expected structure."""
        project_root = Path(__file__).parent.parent
        
        # Check for essential files
        assert (project_root / "pyproject.toml").exists()
        assert (project_root / "README.md").exists()
        
        # Check test structure
        tests_dir = project_root / "tests"
        assert tests_dir.exists()
        assert (tests_dir / "__init__.py").exists()
        assert (tests_dir / "conftest.py").exists()
        assert (tests_dir / "unit").exists()
        assert (tests_dir / "integration").exists()


class TestCoverageSetup:
    """Test class to validate coverage configuration."""
    
    def test_coverage_config_exists(self):
        """Test that coverage configuration is present in pyproject.toml."""
        project_root = Path(__file__).parent.parent
        pyproject_path = project_root / "pyproject.toml"
        
        assert pyproject_path.exists()
        content = pyproject_path.read_text()
        
        assert "[tool.coverage.run]" in content
        assert "[tool.coverage.report]" in content
        assert "[tool.coverage.html]" in content
        assert "[tool.coverage.xml]" in content
    
    def test_pytest_config_exists(self):
        """Test that pytest configuration is present in pyproject.toml."""
        project_root = Path(__file__).parent.parent
        pyproject_path = project_root / "pyproject.toml"
        
        assert pyproject_path.exists()
        content = pyproject_path.read_text()
        
        assert "[tool.pytest.ini_options]" in content
        assert "--cov=" in content
        assert "markers =" in content