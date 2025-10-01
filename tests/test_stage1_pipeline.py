"""
Stage 1: Basic Pipeline Test

Goal: Verify that `make run-test-data` runs without crashing.

This test simply runs the pipeline command and checks it completes successfully.
If this passes, we know the basic pipeline works.
"""

import subprocess


def test_pipeline_runs_without_errors():
    """Test that make run-test-data completes with exit code 0."""

    print("\n=== Stage 1: Testing Pipeline Execution ===")

    # Run the pipeline command
    result = subprocess.run(
        ["make", "run-test-data"],
        capture_output=True,
        text=True,
        timeout=60  # 1 minute timeout
    )

    # Print basic info
    print(f"Exit code: {result.returncode}")

    # Show errors if any
    if result.stderr:
        print(f"STDERR: {result.stderr}")

    # Show last bit of output to confirm completion
    if result.stdout:
        lines = result.stdout.strip().split('\n')
        print(f"Last output line: {lines[-1] if lines else 'No output'}")

    # The test: did it complete without error?
    assert result.returncode == 0, f"Pipeline failed with exit code {result.returncode}"

    print("✓ Pipeline completed successfully")