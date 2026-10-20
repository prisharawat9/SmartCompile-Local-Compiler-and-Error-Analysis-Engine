"""
Tests for Intelligent AI Routing & Optimization Workflow.

Verifies:
  1. Valid code does not trigger an unnecessary AI call.
  2. A locally handled error does not trigger an AI call.
  3. An unresolved issue can be routed to AI.
  4. Only the relevant snippet is sent by default.
  5. A cache hit reuses the stored answer without calling AI.
  6. A cache miss calls the provider when configured.
  9. Mock-provider responses are clearly labeled.
"""

import pytest
from backend.services.router import process_compile_request, CompileRequest
from backend.services.cache import cache_service


@pytest.mark.asyncio
async def test_valid_code_bypasses_ai():
    """Criterion 1: Valid code does not trigger an AI call."""
    code = "def greet(name: str) -> str:\n    return f'Hello {name}'\n"
    req = CompileRequest(source_code=code, language="python")
    resp = await process_compile_request(req)

    assert resp.status == "passed_locally"
    assert resp.resolution_source == "local"
    assert resp.is_mock is False
    assert resp.cache_hit is False
    assert resp.tokens["actual_total_tokens"] == 0
    assert resp.tokens["avoided_by_local"] > 0
    assert resp.request_transparency is None  # Nothing sent to AI!


@pytest.mark.asyncio
async def test_locally_handled_error_bypasses_ai():
    """Criterion 2: Locally handled error does not trigger an AI call."""
    # Missing colon after if statement
    code = "x = 10\nif x > 5\n    print('Greater')\n"
    req = CompileRequest(source_code=code, language="python")
    resp = await process_compile_request(req)

    assert resp.status == "resolved_locally"
    assert resp.resolution_source == "local"
    assert len(resp.local_fixes) >= 1
    assert resp.corrected_code is not None
    assert "if x > 5:" in resp.corrected_code
    assert resp.tokens["actual_total_tokens"] == 0
    assert resp.tokens["avoided_by_local"] > 0
    assert resp.request_transparency is None  # Nothing sent to AI!


@pytest.mark.asyncio
async def test_unresolved_issue_routes_to_ai_and_sends_snippet_only():
    """Criteria 3, 4, 9: Unresolved issue routes to AI, sends snippet only, labels mock."""
    # 20 lines of dummy code with a syntax error in the middle
    lines = [f"var_{i} = {i}" for i in range(1, 10)]
    lines.append("def broken_func(:\n    pass")  # syntax error at line 10
    lines.extend([f"other_{i} = {i}" for i in range(11, 25)])
    full_code = "\n".join(lines)

    req = CompileRequest(source_code=full_code, language="python", provider="mock")
    resp = await process_compile_request(req)

    assert resp.status == "ai_success"
    assert resp.resolution_source == "mock"
    assert resp.is_mock is True
    assert "[SIMULATED MOCK]" in resp.explanation

    # Criterion 4: Verify ONLY the snippet was sent, NOT the entire file!
    assert resp.request_transparency is not None
    transparency = resp.request_transparency
    assert transparency.snippet_char_count < transparency.full_file_char_count
    assert transparency.bytes_saved_pct > 0
    assert "broken_func" in transparency.snippet_sent


@pytest.mark.asyncio
async def test_cache_hit_avoids_ai_call():
    """Criterion 5 & 6: First compile misses cache, second compile hits cache without calling AI."""
    code = "def error_code():\n    return 100 / 0  # ZeroDivision\n"
    req = CompileRequest(source_code=code, language="python", force_ai=True, provider="mock")

    # Call 1: Misses cache, calls provider
    resp1 = await process_compile_request(req)
    assert resp1.status == "ai_success"
    assert resp1.cache_hit is False

    # Call 2: Hits cache
    resp2 = await process_compile_request(req)
    assert resp2.status == "cache_hit"
    assert resp2.resolution_source == "cache"
    assert resp2.cache_hit is True
    assert resp2.cache_details is not None
    assert resp2.cache_details["hit_count"] >= 1
    assert resp2.tokens["avoided_by_cache"] > 0
