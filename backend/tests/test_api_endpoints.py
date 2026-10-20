"""
Tests for FastAPI HTTP Endpoints.

Verifies:
  - POST /api/compile
  - POST /api/analyze
  - GET  /api/stats
  - GET  /api/history
  - GET  /api/cache/stats
  - DELETE /api/cache (with and without confirmation)
  - GET  /api/health (zero secret leakage)
"""

from fastapi.testclient import TestClient


def test_health_endpoint_no_secrets(client: TestClient):
    """Criterion 13: /api/health reports status without exposing API keys or secrets."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("healthy", "degraded")
    assert "active_ai_provider" in data
    assert "api_key_configured" in data
    # Ensure no secret strings or key values are present
    assert "sk-" not in str(data)
    assert "OPENAI_API_KEY" not in str(data)


def test_analyze_endpoint(client: TestClient):
    """Test direct compiler analysis endpoint."""
    res = client.post(
        "/api/analyze",
        json={"source_code": "def hello():\n    return 'world'\n", "language": "python"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "diagnostics" in data["data"]
    assert len(data["data"]["diagnostics"]) == 0


def test_compile_clean_code(client: TestClient):
    """Test /api/compile with clean code."""
    res = client.post(
        "/api/compile",
        json={"source_code": "x = 42\nprint(x)\n", "language": "python"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "passed_locally"
    assert data["resolution_source"] == "local"
    assert data["tokens"]["avoided_by_local"] > 0


def test_compile_local_fix(client: TestClient):
    """Test /api/compile with local deterministic fix."""
    res = client.post(
        "/api/compile",
        json={"source_code": "def test()\n    return True\n", "language": "python"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "resolved_locally"
    assert data["resolution_source"] == "local"
    assert "def test():" in data["corrected_code"]


def test_compile_mock_ai(client: TestClient):
    """Test /api/compile with unresolved error routed to mock AI."""
    res = client.post(
        "/api/compile",
        json={
            "source_code": "def divide(a, b):\n    return a / 0  # Bug\n",
            "language": "python",
            "force_ai": True,
            "provider": "mock",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("ai_success", "cache_hit")
    assert data["is_mock"] is True
    assert data["request_transparency"] is not None
    assert "snippet_sent" in data["request_transparency"]


def test_stats_and_history_backend_backed(client: TestClient):
    """Criterion 11: Dashboard metrics and history come directly from stored database data."""
    # Run a compile first to generate history
    client.post(
        "/api/compile",
        json={"source_code": "print('stats test')\n", "language": "python"},
    )

    # Check /api/stats
    stats_res = client.get("/api/stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["total_compilations"] >= 1
    assert "resolutions" in stats
    assert "savings" in stats
    assert "percentage_reduction" in stats["savings"]

    # Check /api/history
    history_res = client.get("/api/history?limit=10")
    assert history_res.status_code == 200
    hist = history_res.json()
    assert hist["total"] >= 1
    assert len(hist["items"]) >= 1
    assert hist["items"][0]["status"] == "passed_locally"


def test_clear_cache_requires_confirmation(client: TestClient):
    """Criterion 12: Cache clearing fails without confirm=true, succeeds with it."""
    # Attempt without confirmation
    bad_res = client.delete("/api/cache")
    assert bad_res.status_code == 400

    # With confirmation
    good_res = client.delete("/api/cache?confirm=true")
    assert good_res.status_code == 200
    assert good_res.json()["status"] == "success"
