"""
Compiler Module Loader for SmartCompile.

Provides seamless integration between Person 1's compiler module (backend/compiler/analyzer.py)
and Person 2's AI routing/caching system.

If backend/compiler/analyzer.py is implemented with analyze_code, it is dynamically imported.
Otherwise, the realistic local analyzer stub is used with zero disruption.
"""

import importlib
import logging
import os
from typing import Dict, Any, Callable
from .analyzer_stub import analyze_code_stub

logger = logging.getLogger("smartcompile.compiler")

_cached_analyzer_fn: Callable[[str, str], Dict[str, Any]] | None = None
_using_stub = True


def get_analyzer_fn() -> Callable[[str, str], Dict[str, Any]]:
    global _cached_analyzer_fn, _using_stub
    if _cached_analyzer_fn is not None:
        return _cached_analyzer_fn

    # Check if backend/compiler/analyzer.py exists
    current_dir = os.path.dirname(os.path.abspath(__file__))
    real_analyzer_path = os.path.join(current_dir, "analyzer.py")

    if os.path.exists(real_analyzer_path):
        try:
            mod = importlib.import_module("backend.compiler.analyzer")
            if hasattr(mod, "analyze_code") and callable(mod.analyze_code):
                logger.info("Successfully loaded Person 1's compiler engine from backend/compiler/analyzer.py")
                _cached_analyzer_fn = mod.analyze_code
                _using_stub = False
                return _cached_analyzer_fn
            else:
                logger.warning("backend/compiler/analyzer.py found but missing callable analyze_code(source_code, language). Using stub.")
        except Exception as e:
            logger.error(f"Error importing backend/compiler/analyzer.py: {e}. Falling back to stub.")

    logger.info("Using development compiler analyzer stub (backend/compiler/analyzer_stub.py).")
    _cached_analyzer_fn = analyze_code_stub
    _using_stub = True
    return _cached_analyzer_fn


def analyze_code(source_code: str, language: str = "python") -> Dict[str, Any]:
    """Execute compiler error analysis."""
    fn = get_analyzer_fn()
    return fn(source_code, language)


def is_using_stub() -> bool:
    """Return whether the development stub is currently active."""
    get_analyzer_fn()
    return _using_stub
