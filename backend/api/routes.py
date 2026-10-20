"""
FastAPI Routes for SmartCompile.

Implements all required API endpoints:
  - POST /api/compile
  - POST /api/analyze
  - GET  /api/stats
  - GET  /api/history
  - GET  /api/cache/stats
  - DELETE /api/cache
  - GET  /api/health
"""

import json
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.config import settings
from backend.services.router import (
    process_compile_request,
    CompileRequest,
    CompileResponse,
)
from backend.compiler.loader import analyze_code, is_using_stub
from backend.services.cache import cache_service
from backend.services.ai_service import (
    APIKeyMissingError,
    AIRateLimitError,
    AITimeoutError,
    AIProviderError,
)
from backend.db.database import get_db_connection

logger = logging.getLogger("smartcompile.api")

router = APIRouter(prefix="/api")


class AnalyzeRequest(BaseModel):
    source_code: str
    language: str = "python"


class CacheClearResponse(BaseModel):
    status: str
    cleared_entries: int
    message: str


@router.post(
    "/compile",
    response_model=CompileResponse,
    summary="Intelligent compilation & AI optimization pipeline",
)
async def compile_code(req: CompileRequest):
    """
    Execute full optimization workflow:
      1. Local compiler syntax and error analysis
      2. Safe local fix application (0 AI tokens)
      3. SQLite cache lookup (0 AI tokens on hit)
      4. Focused snippet AI request (minimal partial code transmitted)
      5. Token accounting & audit recording
    """
    try:
        response = await process_compile_request(req)
        return response
    except APIKeyMissingError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_type": "APIKeyMissingError",
                "message": str(e),
                "hint": "Set your API key in .env or switch AI_PROVIDER=mock in settings.",
            },
        )
    except AIRateLimitError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"error_type": "AIRateLimitError", "message": str(e)},
        )
    except AITimeoutError as e:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail={"error_type": "AITimeoutError", "message": str(e)},
        )
    except AIProviderError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"error_type": "AIProviderError", "message": str(e)},
        )
    except Exception as e:
        logger.exception("Unexpected error in compile endpoint")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_type": "InternalError", "message": str(e)},
        )


@router.post(
    "/analyze",
    summary="Direct local compiler analysis (Person 1 contract)",
)
async def analyze_code_endpoint(req: AnalyzeRequest):
    """
    Directly invoke the compiler analyzer without AI routing.
    Used for local diagnostics inspection and Person 1 integration verification.
    """
    try:
        result = analyze_code(req.source_code, req.language)
        return {
            "success": True,
            "using_stub": is_using_stub(),
            "data": result,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Compiler analysis error: {str(e)}",
        )


@router.get(
    "/stats",
    summary="Get aggregated token metrics and savings dashboard data",
)
async def get_stats():
    """
    Return comprehensive, real stored metrics:
      - Total compilations
      - Local vs Cache vs AI resolution counts
      - Actual tokens (real provider usage)
      - Simulated tokens (mock provider usage)
      - Non-overlapping avoided tokens (by local, cache, snippet)
      - Percentage reduction vs documented full-file baseline
    """
    conn = get_db_connection()
    try:
        # Total attempts
        total_compilations = conn.execute(
            "SELECT COUNT(*) as c FROM compilation_history"
        ).fetchone()["c"]

        # Counts by resolution source
        source_counts = {
            "local": 0,
            "cache": 0,
            "ai": 0,
            "mock": 0,
        }
        rows = conn.execute(
            "SELECT resolution_source, COUNT(*) as c FROM compilation_history GROUP BY resolution_source"
        ).fetchall()
        for r in rows:
            source = r["resolution_source"]
            if source in source_counts:
                source_counts[source] = r["c"]

        # Real provider actual tokens (EXCLUDING mock)
        actual_tokens_row = conn.execute(
            """
            SELECT 
                COALESCE(SUM(actual_input_tokens), 0) as in_tokens,
                COALESCE(SUM(actual_output_tokens), 0) as out_tokens
            FROM compilation_history
            WHERE resolution_source = 'ai'
            """
        ).fetchone()
        actual_input = actual_tokens_row["in_tokens"]
        actual_output = actual_tokens_row["out_tokens"]
        actual_total = actual_input + actual_output

        # Simulated mock tokens (clearly separated)
        simulated_tokens_row = conn.execute(
            """
            SELECT 
                COALESCE(SUM(estimated_input_tokens), 0) as in_tokens,
                COALESCE(SUM(estimated_output_tokens), 0) as out_tokens
            FROM compilation_history
            WHERE resolution_source = 'mock'
            """
        ).fetchone()
        sim_input = simulated_tokens_row["in_tokens"]
        sim_output = simulated_tokens_row["out_tokens"]
        sim_total = sim_input + sim_output

        # Avoided tokens and baseline totals
        totals_row = conn.execute(
            """
            SELECT 
                COALESCE(SUM(estimated_tokens_saved), 0) as total_saved,
                COALESCE(SUM(baseline_tokens), 0) as total_baseline
            FROM compilation_history
            WHERE status != 'ai_error'
            """
        ).fetchone()
        total_tokens_saved = totals_row["total_saved"]
        total_baseline = totals_row["total_baseline"]

        # Cache statistics
        cache_stats = cache_service.get_stats()

        overall_reduction_pct = 0.0
        if total_baseline > 0:
            overall_reduction_pct = round((total_tokens_saved / total_baseline) * 100.0, 1)

        return {
            "total_compilations": total_compilations,
            "resolutions": source_counts,
            "real_ai": {
                "calls": source_counts["ai"],
                "input_tokens": actual_input,
                "output_tokens": actual_output,
                "total_tokens": actual_total,
            },
            "simulated_mock": {
                "calls": source_counts["mock"],
                "simulated_input_tokens": sim_input,
                "simulated_output_tokens": sim_output,
                "total_simulated_tokens": sim_total,
                "note": "Simulated mock tokens are strictly excluded from real provider usage totals.",
            },
            "cache": cache_stats,
            "savings": {
                "total_tokens_saved": total_tokens_saved,
                "baseline_tokens": total_baseline,
                "percentage_reduction": overall_reduction_pct,
                "baseline_definition": (
                    "Full-File Baseline: sending entire source code file plus 250 prompt overhead tokens "
                    "and 180 expected completion tokens on every compilation attempt."
                ),
            },
        }
    finally:
        conn.close()


@router.get(
    "/history",
    summary="Get recent compilation runs",
)
async def get_history(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """Return chronological history of compilation attempts with audit metadata."""
    conn = get_db_connection()
    try:
        rows = conn.execute(
            """
            SELECT 
                id, timestamp, language, status, resolution_source,
                ai_provider, ai_model, actual_input_tokens, actual_output_tokens,
                estimated_input_tokens, estimated_output_tokens, estimated_tokens_saved,
                baseline_tokens, explanation, corrected_code, request_payload_json,
                diagnostics_json, local_fixes_json, error_message,
                SUBSTR(source_code, 1, 200) as source_preview
            FROM compilation_history
            ORDER BY id DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()

        items = []
        for r in rows:
            items.append({
                "id": r["id"],
                "timestamp": r["timestamp"],
                "language": r["language"],
                "status": r["status"],
                "resolution_source": r["resolution_source"],
                "ai_provider": r["ai_provider"],
                "ai_model": r["ai_model"],
                "actual_input_tokens": r["actual_input_tokens"],
                "actual_output_tokens": r["actual_output_tokens"],
                "estimated_tokens_saved": r["estimated_tokens_saved"],
                "baseline_tokens": r["baseline_tokens"],
                "explanation": r["explanation"],
                "corrected_code": r["corrected_code"],
                "source_preview": r["source_preview"],
                "diagnostics": json.loads(r["diagnostics_json"]) if r["diagnostics_json"] else [],
                "local_fixes": json.loads(r["local_fixes_json"]) if r["local_fixes_json"] else [],
                "request_transparency": json.loads(r["request_payload_json"]) if r["request_payload_json"] else None,
                "error_message": r["error_message"],
            })

        total = conn.execute("SELECT COUNT(*) as c FROM compilation_history").fetchone()["c"]
        return {"items": items, "total": total, "limit": limit, "offset": offset}
    finally:
        conn.close()


@router.get(
    "/cache/stats",
    summary="Get detailed cache performance metrics",
)
async def get_cache_stats():
    """Return persistent cache size, hit/miss numbers, and hit rate."""
    return cache_service.get_stats()


@router.delete(
    "/cache",
    response_model=CacheClearResponse,
    summary="Clear persistent SQLite response cache",
)
async def clear_cache(
    confirm: bool = Query(
        default=False,
        description="Must be set to True to confirm clearing cache entries.",
    )
):
    """
    Clear all cached AI responses with explicit confirmation.
    """
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Confirmation required to clear cache. Pass confirm=true.",
        )
    result = cache_service.clear()
    return CacheClearResponse(
        status="success",
        cleared_entries=result["cleared_entries"],
        message=f"Cache cleared successfully. Removed {result['cleared_entries']} stored entries.",
    )


@router.get(
    "/health",
    summary="Application and AI provider configuration status",
)
async def health_check():
    """
    Report application configuration, provider availability, and compiler status.
    NEVER exposes secrets or actual API keys.
    """
    active_prov = settings.active_provider
    has_key = settings.has_api_key_for_provider(active_prov)

    # Active model name
    model = (
        settings.OPENAI_MODEL if active_prov == "openai"
        else settings.GEMINI_MODEL if active_prov == "gemini"
        else settings.ANTHROPIC_MODEL if active_prov == "anthropic"
        else "mock-smartcompile-v1"
    )

    # Test SQLite connection
    db_healthy = True
    try:
        conn = get_db_connection()
        conn.execute("SELECT 1").fetchone()
        conn.close()
    except Exception:
        db_healthy = False

    return {
        "status": "healthy" if db_healthy else "degraded",
        "app": "SmartCompile",
        "version": "1.0.0",
        "active_ai_provider": active_prov,
        "active_model": model,
        "api_key_configured": has_key,
        "is_mock_provider": active_prov == "mock",
        "database_connected": db_healthy,
        "compiler_engine_using_stub": is_using_stub(),
    }
