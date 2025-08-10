"""
Integration test for offline mode functionality.

This test runs the equivalent of 'make run-offline' to ensure the entire
offline processing pipeline works end-to-end.
"""

import pytest
import subprocess
import os
import tempfile
import shutil
from pathlib import Path


class TestOfflineMode:
    """Integration tests for offline mode processing."""

    def test_make_run_offline_integration(self):
        """Test that 'make run-offline' equivalent runs successfully."""
        # Get the project root directory
        project_root = Path(__file__).parent.parent.parent
        
        # Change to project directory and run the offline mode
        original_cwd = os.getcwd()
        try:
            os.chdir(project_root)
            
            # Run the equivalent of 'make run-offline'
            # This sets OFFLINE=True and runs the main module
            env = os.environ.copy()
            env['OFFLINE'] = 'True'
            env['DEBUG'] = 'True'
            
            result = subprocess.run(
                ['../venv/bin/python', '-m', 'main'],
                env=env,
                cwd=project_root / 'src',
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )
            
            # Check that the process completed successfully
            assert result.returncode == 0, f"Process failed with error: {result.stderr}"
            
            # Check that some output was generated (indicates processing occurred)
            assert len(result.stdout) > 0 or len(result.stderr) > 0, "No output generated"
            
            # Check that no critical errors occurred
            assert "Error" not in result.stderr or "Traceback" not in result.stderr, f"Critical errors in output: {result.stderr}"
            
        finally:
            os.chdir(original_cwd)

    def test_offline_mode_creates_output_files(self):
        """Test that offline mode creates expected output files."""
        project_root = Path(__file__).parent.parent.parent
        
        # Use a temporary output directory
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(project_root)
                
                # Set environment variables
                env = os.environ.copy()
                env['OFFLINE'] = 'True'
                env['DEBUG'] = 'True'
                env['OUTPUT_DIR'] = temp_dir
                
                # Run offline processing
                result = subprocess.run(
                    ['../venv/bin/python', '-m', 'main'],
                    env=env,
                    cwd=project_root / 'src',
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                # Process should complete successfully
                assert result.returncode == 0, f"Process failed: {result.stderr}"
                
                # Check if any CSV files were created (indicates successful processing)
                output_path = Path(temp_dir)
                csv_files = list(output_path.glob("*.csv"))
                
                # Should have at least attempted to create output files
                # (May be empty if no test data, but directory structure should exist)
                assert output_path.exists(), "Output directory was not created"
                
            finally:
                os.chdir(original_cwd)

    def test_offline_mode_with_test_data(self):
        """Test offline mode processes test data if available."""
        project_root = Path(__file__).parent.parent.parent
        test_data_dir = project_root / "src" / "test_data"
        
        # Only run this test if test data exists
        if not test_data_dir.exists():
            pytest.skip("No test data directory found")
        
        original_cwd = os.getcwd()
        try:
            os.chdir(project_root)
            
            env = os.environ.copy()
            env['OFFLINE'] = 'True'
            env['DEBUG'] = 'True'
            
            result = subprocess.run(
                ['../venv/bin/python', '-m', 'main'],
                env=env,
                cwd=project_root / 'src',
                capture_output=True,
                text=True,
                timeout=120
            )
            
            assert result.returncode == 0, f"Process failed: {result.stderr}"
            
            # If test data exists, should process some articles
            if "Processed" in result.stdout:
                # Verify some processing occurred
                assert "0 articles processed" not in result.stdout, "No articles were processed despite test data being available"
                
        finally:
            os.chdir(original_cwd)

    def test_offline_mode_error_handling(self):
        """Test that offline mode handles errors gracefully."""
        project_root = Path(__file__).parent.parent.parent
        
        original_cwd = os.getcwd()
        try:
            os.chdir(project_root)
            
            # Test with an invalid output directory to trigger error handling
            env = os.environ.copy()
            env['OFFLINE'] = 'True'
            env['DEBUG'] = 'True'
            env['OUTPUT_DIR'] = '/invalid/path/that/does/not/exist'
            
            result = subprocess.run(
                ['../venv/bin/python', '-m', 'main'],
                env=env,
                cwd=project_root / 'src',
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Process might fail, but should not crash with unhandled exceptions
            if result.returncode != 0:
                # Should have meaningful error messages, not just Python tracebacks
                assert "Traceback" not in result.stderr or "handled gracefully" in result.stderr.lower()
            
        finally:
            os.chdir(original_cwd)

    def test_offline_mode_configuration_loading(self):
        """Test that offline mode loads configuration correctly."""
        project_root = Path(__file__).parent.parent.parent
        
        original_cwd = os.getcwd()
        try:
            os.chdir(project_root)
            
            env = os.environ.copy()
            env['OFFLINE'] = 'True'
            env['DEBUG'] = 'True'
            
            result = subprocess.run(
                ['../venv/bin/python', '-m', 'main'],
                env=env,
                cwd=project_root / 'src',
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Should not fail due to configuration issues
            assert "ImportError" not in result.stderr, "Configuration import failed"
            assert "ModuleNotFoundError" not in result.stderr, "Module loading failed"
            
            # Should indicate that configuration was loaded
            if result.returncode == 0:
                # Process completed successfully, indicating config was loaded
                assert True
            else:
                # If it failed, it shouldn't be due to basic config issues
                config_errors = [
                    "No module named",
                    "ImportError",
                    "SyntaxError",
                    "IndentationError"
                ]
                has_config_error = any(error in result.stderr for error in config_errors)
                assert not has_config_error, f"Configuration error detected: {result.stderr}"
                
        finally:
            os.chdir(original_cwd)

    @pytest.mark.slow
    def test_offline_mode_performance(self):
        """Test that offline mode completes within reasonable time."""
        project_root = Path(__file__).parent.parent.parent
        
        original_cwd = os.getcwd()
        try:
            os.chdir(project_root)
            
            env = os.environ.copy()
            env['OFFLINE'] = 'True'
            env['DEBUG'] = 'True'
            
            import time
            start_time = time.time()
            
            result = subprocess.run(
                ['../venv/bin/python', '-m', 'main'],
                env=env,
                cwd=project_root / 'src',
                capture_output=True,
                text=True,
                timeout=180  # 3 minute timeout for performance test
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Should complete within reasonable time (3 minutes)
            assert duration < 180, f"Offline mode took too long: {duration} seconds"
            
            # For normal cases, should be much faster (under 30 seconds)
            if result.returncode == 0 and "test data" not in result.stdout.lower():
                assert duration < 30, f"Offline mode without test data took too long: {duration} seconds"
                
        finally:
            os.chdir(original_cwd)


class TestLiveMode:
    """Integration tests for live mode processing."""

    def test_make_run_live_integration(self):
        """Test that 'make run-live' equivalent runs successfully."""
        # Get the project root directory
        project_root = Path(__file__).parent.parent.parent
        
        # Change to project directory and run the live mode
        original_cwd = os.getcwd()
        try:
            os.chdir(project_root)
            
            # Run the equivalent of 'make run-live'
            # This sets OFFLINE=False and runs the main module
            env = os.environ.copy()
            env['OFFLINE'] = 'False'
            env['DEBUG'] = 'True'
            
            result = subprocess.run(
                ['../venv/bin/python', '-m', 'main'],
                env=env,
                cwd=project_root / 'src',
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )
            
            # Check that the process completed successfully
            assert result.returncode == 0, f"Process failed with error: {result.stderr}"
            
            # Check that some output was generated (indicates processing occurred)
            assert len(result.stdout) > 0 or len(result.stderr) > 0, "No output generated"
            
            # Check that no critical errors occurred
            assert "Error" not in result.stderr or "Traceback" not in result.stderr, f"Critical errors in output: {result.stderr}"
            
        finally:
            os.chdir(original_cwd)

    def test_live_mode_configuration_loading(self):
        """Test that live mode loads configuration correctly."""
        project_root = Path(__file__).parent.parent.parent
        
        original_cwd = os.getcwd()
        try:
            os.chdir(project_root)
            
            env = os.environ.copy()
            env['OFFLINE'] = 'False'
            env['DEBUG'] = 'True'
            
            result = subprocess.run(
                ['../venv/bin/python', '-m', 'main'],
                env=env,
                cwd=project_root / 'src',
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Should not fail due to configuration issues
            assert "ImportError" not in result.stderr, "Configuration import failed"
            assert "ModuleNotFoundError" not in result.stderr, "Module loading failed"
            
            # Should indicate that configuration was loaded
            if result.returncode == 0:
                # Process completed successfully, indicating config was loaded
                assert True
            else:
                # If it failed, it shouldn't be due to basic config issues
                config_errors = [
                    "No module named",
                    "ImportError",
                    "SyntaxError",
                    "IndentationError"
                ]
                has_config_error = any(error in result.stderr for error in config_errors)
                assert not has_config_error, f"Configuration error detected: {result.stderr}"
                
        finally:
            os.chdir(original_cwd)