from __future__ import annotations
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from run import main

if __name__ == "__main__":
    main()

