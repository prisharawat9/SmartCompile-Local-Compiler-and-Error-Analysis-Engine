"""
Tests for Persistent Cache Service & Invalidation Logic.

Verifies:
  - Cache key stability under whitespace changes
  - Collision prevention for different errors
  - Invalidation when model or settings change
  - Clear cache functionality (Criterion 12)
"""

from backend.services.cache import (
    cache_service,
    generate_cache_key,
    normalize_code_snippet,
)


def test_normalize_code_snippet():
    """Ensure line endings and line number markers are stripped consistently."""
    snippet_with_markers = ">> 14 |     def test():\n   15 |         return 42\n"
    normalized = normalize_code_snippet(snippet_with_markers)
    assert ">>" not in normalized
    assert "14 |" not in normalized
    assert "def test():" in normalized


def test_cache_key_stability():
    """Equivalent snippets should produce the identical SHA-256 key."""
    snip1 = "    def calc(a, b):\n        return a + b    \n"
    snip2 = "def calc(a, b):\n    return a + b\n"
    k1 = generate_cache_key(snip1, "ZeroDivisionError", "runtime", "python", "gpt-4o-mini", "openai")
    k2 = generate_cache_key(snip2, "ZeroDivisionError", "runtime", "python", "gpt-4o-mini", "openai")
    # Both normalize to the same code
    assert k1 == k2


def test_cache_key_differentiation():
    """Different models, diagnostics, or code must produce different cache keys (no collision)."""
    k_base = generate_cache_key("x = 1", "Error 1", "syntax", "python", "gpt-4o-mini", "openai")
    k_diff_model = generate_cache_key("x = 1", "Error 1", "syntax", "python", "claude-3-5", "anthropic")
    k_diff_diag = generate_cache_key("x = 1", "Error 2", "syntax", "python", "gpt-4o-mini", "openai")
    k_diff_code = generate_cache_key("y = 2", "Error 1", "syntax", "python", "gpt-4o-mini", "openai")

    assert k_base != k_diff_model
    assert k_base != k_diff_diag
    assert k_base != k_diff_code


def test_cache_set_and_get():
    """Store entry, verify retrieval and hit counter increment."""
    key = "test_key_123"
    cache_service.set(
        cache_key=key,
        snippet="snippet",
        diagnostic_msg="SyntaxError",
        language="python",
        model="mock-v1",
        provider="mock",
        prompt_sent="prompt",
        response_explanation="Test explanation",
        response_fix="fixed_code()",
        tokens_input=10,
        tokens_output=20,
        is_mock=True,
    )

    entry = cache_service.get(key)
    assert entry is not None
    assert entry.explanation == "Test explanation"
    assert entry.hit_count == 1

    entry2 = cache_service.get(key)
    assert entry2.hit_count == 2


def test_clear_cache():
    """Criterion 12: Clearing the cache empties the store."""
    cache_service.set(
        cache_key="key_to_delete",
        snippet="code",
        diagnostic_msg="msg",
        language="python",
        model="m",
        provider="p",
        prompt_sent="p",
        response_explanation="exp",
        response_fix="fix",
    )
    assert cache_service.get("key_to_delete") is not None

    clear_res = cache_service.clear()
    assert clear_res["status"] == "success"
    assert clear_res["cleared_entries"] >= 1

    # Should now be a cache miss
    assert cache_service.get("key_to_delete") is None
