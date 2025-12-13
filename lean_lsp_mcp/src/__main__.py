"""Entry point for running lean_lsp_mcp as a module."""
import sys
import os

# Ensure the src directory is in the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import from the local package
from __init__ import main

if __name__ == "__main__":
    sys.exit(main())
