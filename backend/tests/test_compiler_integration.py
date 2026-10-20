"""
Tests for Compiler Engine Integration and Contract.
Verifies Person 1 interface compliance and stub behavior.
"""

from backend.compiler.loader import analyze_code, is_using_stub
from backend.compiler.interface import AnalysisResult


def test_clean_valid_code_analysis():
    """Valid Python code should produce 0 diagnostics and not need AI."""
    code = "def add(a, b):\n    return a + b\n"
    res = analyze_code(code, "python")
    assert isinstance(res, dict)
    assert len(res["diagnostics"]) == 0
    assert res["needs_ai"] is False
    assert res["corrected_code"] == code
    assert res["analysis_summary"]["total_errors"] == 0
    assert res["analysis_summary"]["resolved_locally"] is True


def test_local_fix_missing_colon():
    """Missing colon after 'def' statement should be detected and locally resolved."""
    broken_code = "def calculate_area(width, height)\n    return width * height\n"
    res = analyze_code(broken_code, "python")
    assert len(res["diagnostics"]) >= 1
    assert len(res["local_fixes"]) == 1
    assert res["needs_ai"] is False  # Local fix resolved it!
    assert res["corrected_code"] is not None
    assert "def calculate_area(width, height):" in res["corrected_code"]
    assert res["analysis_summary"]["resolved_locally"] is True


def test_unresolved_error_triggers_needs_ai():
    """Complex syntax error that cannot be locally fixed must set needs_ai=True and provide snippet."""
    unresolved_code = "def broken():\n    x = ))))invalid(((\n"
    res = analyze_code(unresolved_code, "python")
    assert len(res["diagnostics"]) >= 1
    assert res["needs_ai"] is True
    assert res["corrected_code"] is None
    assert res["relevant_snippet"] is not None
    assert "broken" in res["relevant_snippet"] or "invalid" in res["relevant_snippet"]
