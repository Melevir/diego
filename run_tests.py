#!/usr/bin/env python3
"""
Simple test runner script for Diego News CLI.

This script runs the test suite and provides a summary of results.
"""

import subprocess
import sys


def run_tests():
    """Run the test suite with coverage."""
    print("🚀 Running Diego News CLI Test Suite...")
    print("=" * 50)

    try:
        # Run tests with coverage
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "--cov=.", "--cov-report=term-missing", "--verbose"],
            capture_output=False,
            text=True,
        )

        if result.returncode == 0:
            print("\n✅ All tests passed!")
            print("🎉 Diego News CLI is ready for use!")
        else:
            print(f"\n❌ Tests failed with exit code: {result.returncode}")
            sys.exit(1)

    except FileNotFoundError:
        print("❌ pytest not found. Install dependencies first:")
        print("pip3 install -r requirements-test.txt")
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
