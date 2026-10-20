"""
Tests for Token Accounting & Baseline Savings Calculations.

Verifies:
  10. Token usage and estimated savings use consistent calculations.
  - Baseline definition is documented and positive.
  - Non-overlapping savings categories (no double counting).
"""

from backend.services.token_accounting import (
    estimate_tokens,
    calculate_full_file_baseline,
    compute_savings,
)


def test_token_estimation_positive():
    """Token estimation should return positive, proportional estimates."""
    short_code = "x = 1"
    long_code = "def fib(n):\n    if n <= 1:\n        return n\n    return fib(n-1) + fib(n-2)\n" * 10
    assert estimate_tokens(short_code) > 0
    assert estimate_tokens(long_code) > estimate_tokens(short_code)


def test_baseline_calculation_consistency():
    """Full-file baseline should add file tokens + prompt overhead + expected output."""
    code = "import math\nprint(math.pi)\n"
    base = calculate_full_file_baseline(code)
    assert base["full_file_tokens"] > 0
    assert base["baseline_input"] > base["full_file_tokens"]
    assert base["baseline_total"] == base["baseline_input"] + base["baseline_output"]


def test_local_resolution_savings_non_overlapping():
    """Local resolution should credit avoided_by_local without touching cache or snippet avoided."""
    code = "def add(a, b):\n    return a + b\n"
    savings = compute_savings(code, resolution_source="local")

    assert savings["avoided_by_local"] == savings["baseline_tokens"]
    assert savings["avoided_by_cache"] == 0
    assert savings["avoided_by_snippet"] == 0
    assert savings["total_tokens_saved"] == savings["avoided_by_local"]
    assert savings["reduction_percentage"] == 100.0


def test_cache_hit_savings_non_overlapping():
    """Cache hit should credit avoided_by_cache without touching local or snippet avoided."""
    code = "x = 10 / 0\n"
    savings = compute_savings(code, resolution_source="cache")

    assert savings["avoided_by_cache"] == savings["baseline_tokens"]
    assert savings["avoided_by_local"] == 0
    assert savings["avoided_by_snippet"] == 0
    assert savings["total_tokens_saved"] == savings["avoided_by_cache"]


def test_snippet_ai_savings():
    """When AI is called with only snippet, savings should equal max(0, baseline - actual_used)."""
    full_code = "def foo():\n    pass\n" * 50  # Large file
    savings = compute_savings(
        source_code=full_code,
        resolution_source="ai",
        snippet_text="def foo():\n    pass",
        actual_input_tokens=50,
        actual_output_tokens=30,
        is_mock=False,
    )

    actual_used = 50 + 30
    assert savings["avoided_by_snippet"] == max(0, savings["baseline_tokens"] - actual_used)
    assert savings["total_tokens_saved"] == savings["avoided_by_snippet"]
    assert savings["is_mock"] is False
    assert savings["is_estimated"] is False
