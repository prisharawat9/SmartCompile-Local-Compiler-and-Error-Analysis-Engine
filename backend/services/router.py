"""
Intelligent AI Routing Engine for SmartCompile.

Implements the multi-stage optimization pipeline:
  1. Local Compiler Analysis (Person 1's engine or stub)
  2. Safe Local Fix Evaluation (bypasses AI entirely if local fix succeeds)
  3. Persistent SQLite Cache Lookup (bypasses AI if cached snippet match exists)
  4. Partial Snippet Transmission to AI Provider (sends ONLY the snippet + minimal context)
  5. Token Accounting, Savings Metrics & Audit History Recording
"""

from datetime import datetime, timezone
import json
import logging
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from backend.compiler.loader import analyze_code, is_using_stub
from backend.services.prompt_builder import build_focused_ai_payload
from backend.services.cache import cache_service, generate_cache_key
from backend.services.ai_service import (
    get_ai_provider,
    AIResponse,
    APIKeyMissingError,
    AIRateLimitError,
    AITimeoutError,
    AIProviderError,
)
from backend.services.token_accounting import (
    calculate_full_file_baseline,
    compute_savings,
    estimate_tokens,
)
from backend.db.database import get_db_connection
from backend.config import settings

logger = logging.getLogger("smartcompile.router")


class CompileRequest(BaseModel):
    source_code: str = Field(..., description="Source code to compile and analyze")
    language: str = Field(default="python", description="Language of the source code")
    force_ai: bool = Field(default=False, description="Explicitly request AI analysis even if code passes")
    provider: Optional[str] = Field(default=None, description="Optional provider override ('mock', 'openai', etc.)")
    model: Optional[str] = Field(default=None, description="Optional model override")


class TransparencyDetails(BaseModel):
    system_prompt: str
    user_prompt: str
    snippet_sent: str
    line_start: int
    line_end: int
    full_file_char_count: int
    snippet_char_count: int
    prompt_tokens_est: int
    bytes_saved_pct: float


class CompileResponse(BaseModel):
    status: str = Field(..., description="'passed_locally', 'resolved_locally', 'cache_hit', 'ai_success', 'ai_error'")
    resolution_source: str = Field(..., description="'local', 'cache', 'ai', 'mock'")
    language: str
    diagnostics: List[Dict[str, Any]]
    local_fixes: List[Dict[str, Any]]
    corrected_code: Optional[str]
    explanation: str
    suggested_fix: Optional[str] = None
    ai_provider: Optional[str] = None
    ai_model: Optional[str] = None
    is_mock: bool = False
    tokens: Dict[str, Any]
    cache_hit: bool = False
    cache_details: Optional[Dict[str, Any]] = None
    request_transparency: Optional[TransparencyDetails] = None
    error: Optional[str] = None


def record_compilation_history(record: Dict[str, Any]) -> int:
    """Save compilation record to SQLite history table."""
    conn = get_db_connection()
    try:
        now_iso = datetime.now(timezone.utc).isoformat()
        with conn:
            cur = conn.execute(
                """
                INSERT INTO compilation_history (
                    timestamp, language, source_code, full_code_tokens_est,
                    snippet_tokens_est, diagnostics_json, local_fixes_json,
                    status, resolution_source, ai_provider, ai_model,
                    actual_input_tokens, actual_output_tokens, estimated_input_tokens,
                    estimated_output_tokens, estimated_tokens_saved, baseline_tokens,
                    explanation, corrected_code, request_payload_json, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    now_iso,
                    record.get("language", "python"),
                    record.get("source_code", ""),
                    record.get("full_code_tokens_est", 0),
                    record.get("snippet_tokens_est", 0),
                    json.dumps(record.get("diagnostics", [])),
                    json.dumps(record.get("local_fixes", [])),
                    record.get("status", "unknown"),
                    record.get("resolution_source", "local"),
                    record.get("ai_provider"),
                    record.get("ai_model"),
                    record.get("actual_input_tokens", 0),
                    record.get("actual_output_tokens", 0),
                    record.get("estimated_input_tokens", 0),
                    record.get("estimated_output_tokens", 0),
                    record.get("estimated_tokens_saved", 0),
                    record.get("baseline_tokens", 0),
                    record.get("explanation", ""),
                    record.get("corrected_code"),
                    json.dumps(record.get("request_transparency")) if record.get("request_transparency") else None,
                    record.get("error_message"),
                ),
            )
            return cur.lastrowid
    finally:
        conn.close()


async def process_compile_request(req: CompileRequest) -> CompileResponse:
    source_code = req.source_code
    language = req.language
    force_ai = req.force_ai
    provider_name = req.provider or settings.active_provider
    model_name = req.model

    # Step 1: Run Local Compiler Analysis
    compiler_out = analyze_code(source_code, language)
    diagnostics = compiler_out.get("diagnostics", [])
    local_fixes = compiler_out.get("local_fixes", [])
    corrected_code = compiler_out.get("corrected_code")
    needs_ai = compiler_out.get("needs_ai", False)
    relevant_snippet = compiler_out.get("relevant_snippet")

    # Step 2: Handle Code That Passed Local Analysis (No errors)
    if not diagnostics and not force_ai:
        savings = compute_savings(
            source_code=source_code,
            resolution_source="local",
        )
        explanation = "Code passed local compiler analysis with 0 errors. No AI call required."
        record_compilation_history({
            "language": language,
            "source_code": source_code,
            "full_code_tokens_est": savings["full_file_tokens_est"],
            "snippet_tokens_est": 0,
            "diagnostics": [],
            "local_fixes": [],
            "status": "passed_locally",
            "resolution_source": "local",
            "baseline_tokens": savings["baseline_tokens"],
            "estimated_tokens_saved": savings["total_tokens_saved"],
            "explanation": explanation,
            "corrected_code": source_code,
        })
        return CompileResponse(
            status="passed_locally",
            resolution_source="local",
            language=language,
            diagnostics=[],
            local_fixes=[],
            corrected_code=source_code,
            explanation=explanation,
            tokens=savings,
            cache_hit=False,
        )

    # Step 3: Handle Safe Local Fixes (No AI call required)
    if local_fixes and not needs_ai and not force_ai and corrected_code:
        savings = compute_savings(
            source_code=source_code,
            resolution_source="local",
        )
        fix_desc = local_fixes[0].get("description", "Deterministic local fix applied")
        explanation = f"Resolved locally by compiler: {fix_desc}. AI call bypassed."
        record_compilation_history({
            "language": language,
            "source_code": source_code,
            "full_code_tokens_est": savings["full_file_tokens_est"],
            "snippet_tokens_est": 0,
            "diagnostics": diagnostics,
            "local_fixes": local_fixes,
            "status": "resolved_locally",
            "resolution_source": "local",
            "baseline_tokens": savings["baseline_tokens"],
            "estimated_tokens_saved": savings["total_tokens_saved"],
            "explanation": explanation,
            "corrected_code": corrected_code,
        })
        return CompileResponse(
            status="resolved_locally",
            resolution_source="local",
            language=language,
            diagnostics=diagnostics,
            local_fixes=local_fixes,
            corrected_code=corrected_code,
            explanation=explanation,
            suggested_fix=local_fixes[0].get("replacement"),
            tokens=savings,
            cache_hit=False,
        )

    # Step 4: AI Assistance Required (Construct focused payload with partial code)
    ai_provider = get_ai_provider(provider_name)
    actual_provider_name = ai_provider.name
    active_model = model_name or (
        settings.OPENAI_MODEL if actual_provider_name == "openai"
        else settings.GEMINI_MODEL if actual_provider_name == "gemini"
        else settings.ANTHROPIC_MODEL if actual_provider_name == "anthropic"
        else "mock-smartcompile-v1"
    )

    payload = build_focused_ai_payload(
        source_code=source_code,
        language=language,
        diagnostics=diagnostics,
        provided_snippet=relevant_snippet,
        context_window=3,
    )

    transparency = TransparencyDetails(
        system_prompt=payload["system_prompt"],
        user_prompt=payload["user_prompt"],
        snippet_sent=payload["snippet_text"],
        line_start=payload["line_start"],
        line_end=payload["line_end"],
        full_file_char_count=payload["full_file_char_count"],
        snippet_char_count=payload["snippet_char_count"],
        prompt_tokens_est=payload["prompt_tokens_est"],
        bytes_saved_pct=round(
            max(0.0, 100.0 - (payload["snippet_char_count"] / max(1, payload["full_file_char_count"]) * 100.0)),
            1,
        ),
    )

    # Step 5: Check Persistent Cache
    cache_key = generate_cache_key(
        snippet=payload["snippet_text"],
        diagnostic_msg=payload["diagnostic_message"],
        category=payload["diagnostic_category"],
        language=language,
        model=active_model,
        provider=actual_provider_name,
    )

    cached_entry = cache_service.get(cache_key)
    if cached_entry:
        savings = compute_savings(
            source_code=source_code,
            resolution_source="cache",
            snippet_text=payload["snippet_text"],
            prompt_sent=payload["combined_prompt"],
        )
        record_compilation_history({
            "language": language,
            "source_code": source_code,
            "full_code_tokens_est": savings["full_file_tokens_est"],
            "snippet_tokens_est": savings["snippet_tokens_est"],
            "diagnostics": diagnostics,
            "local_fixes": local_fixes,
            "status": "cache_hit",
            "resolution_source": "cache",
            "ai_provider": cached_entry.provider,
            "ai_model": cached_entry.model,
            "baseline_tokens": savings["baseline_tokens"],
            "estimated_tokens_saved": savings["total_tokens_saved"],
            "explanation": f"[CACHED RESPONSE] {cached_entry.explanation}",
            "corrected_code": cached_entry.suggested_fix,
            "request_transparency": transparency.model_dump(),
        })
        return CompileResponse(
            status="cache_hit",
            resolution_source="cache",
            language=language,
            diagnostics=diagnostics,
            local_fixes=local_fixes,
            corrected_code=cached_entry.suggested_fix,
            explanation=cached_entry.explanation,
            suggested_fix=cached_entry.suggested_fix,
            ai_provider=cached_entry.provider,
            ai_model=cached_entry.model,
            is_mock=cached_entry.is_mock,
            tokens=savings,
            cache_hit=True,
            cache_details={
                "cache_key": cached_entry.cache_key,
                "hit_count": cached_entry.hit_count,
                "created_at": cached_entry.created_at,
                "reason": cached_entry.cache_hit_reason,
            },
            request_transparency=transparency,
        )

    # Step 6: Cache Miss - Dispatch to AI Provider
    try:
        ai_resp: AIResponse = await ai_provider.generate_correction(payload, model_override=active_model)
    except APIKeyMissingError as e:
        record_compilation_history({
            "language": language,
            "source_code": source_code,
            "full_code_tokens_est": estimate_tokens(source_code),
            "diagnostics": diagnostics,
            "status": "ai_error",
            "resolution_source": "ai",
            "ai_provider": actual_provider_name,
            "error_message": str(e),
            "request_transparency": transparency.model_dump(),
        })
        raise
    except (AIRateLimitError, AITimeoutError, AIProviderError) as e:
        record_compilation_history({
            "language": language,
            "source_code": source_code,
            "full_code_tokens_est": estimate_tokens(source_code),
            "diagnostics": diagnostics,
            "status": "ai_error",
            "resolution_source": "ai",
            "ai_provider": actual_provider_name,
            "error_message": str(e),
            "request_transparency": transparency.model_dump(),
        })
        raise

    # Store in Cache
    cache_service.set(
        cache_key=cache_key,
        snippet=payload["snippet_text"],
        diagnostic_msg=payload["diagnostic_message"],
        language=language,
        model=ai_resp.model,
        provider=ai_resp.provider,
        prompt_sent=payload["combined_prompt"],
        response_explanation=ai_resp.explanation,
        response_fix=ai_resp.suggested_fix,
        tokens_input=ai_resp.input_tokens,
        tokens_output=ai_resp.output_tokens,
        is_mock=ai_resp.is_mock,
    )

    # Step 7: Token Accounting & History
    resolution_source = "mock" if ai_resp.is_mock else "ai"
    savings = compute_savings(
        source_code=source_code,
        resolution_source=resolution_source,
        snippet_text=payload["snippet_text"],
        prompt_sent=payload["combined_prompt"],
        actual_input_tokens=0 if ai_resp.is_mock else ai_resp.input_tokens,
        actual_output_tokens=0 if ai_resp.is_mock else ai_resp.output_tokens,
        is_mock=ai_resp.is_mock,
    )

    record_compilation_history({
        "language": language,
        "source_code": source_code,
        "full_code_tokens_est": savings["full_file_tokens_est"],
        "snippet_tokens_est": savings["snippet_tokens_est"],
        "diagnostics": diagnostics,
        "local_fixes": local_fixes,
        "status": "ai_success",
        "resolution_source": resolution_source,
        "ai_provider": ai_resp.provider,
        "ai_model": ai_resp.model,
        "actual_input_tokens": 0 if ai_resp.is_mock else ai_resp.input_tokens,
        "actual_output_tokens": 0 if ai_resp.is_mock else ai_resp.output_tokens,
        "estimated_input_tokens": ai_resp.input_tokens if ai_resp.is_mock else 0,
        "estimated_output_tokens": ai_resp.output_tokens if ai_resp.is_mock else 0,
        "baseline_tokens": savings["baseline_tokens"],
        "estimated_tokens_saved": savings["total_tokens_saved"],
        "explanation": ai_resp.explanation,
        "corrected_code": ai_resp.suggested_fix,
        "request_transparency": transparency.model_dump(),
    })

    return CompileResponse(
        status="ai_success",
        resolution_source=resolution_source,
        language=language,
        diagnostics=diagnostics,
        local_fixes=local_fixes,
        corrected_code=ai_resp.corrected_snippet or ai_resp.suggested_fix,
        explanation=ai_resp.explanation,
        suggested_fix=ai_resp.suggested_fix,
        ai_provider=ai_resp.provider,
        ai_model=ai_resp.model,
        is_mock=ai_resp.is_mock,
        tokens=savings,
        cache_hit=False,
        request_transparency=transparency,
    )
