import os
import sys

# Tests run against the src/ layout directly, without requiring the
# package to be installed first.
_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)
