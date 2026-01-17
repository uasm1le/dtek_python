"""Tests for main module."""

import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from main import hello


def test_hello():
    """Test the hello function."""
    result = hello()
    assert result == "Hello, World!"


if __name__ == "__main__":
    test_hello()
    print("All tests passed!")
