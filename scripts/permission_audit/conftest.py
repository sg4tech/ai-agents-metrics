"""Pytest configuration for input/ test suite."""

import sys
from pathlib import Path

# Ensure input/ is importable without installing as a package.
sys.path.insert(0, str(Path(__file__).resolve().parent))
