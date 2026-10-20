"""
Token Accounting & Baseline Savings Calculation for SmartCompile.

Provides rigorous, transparent token accounting and savings metrics.
Guarantees:
  - Clear separation between actual provider-reported tokens, simulated mock tokens, and estimated tokens.
  - Transparent documentation of the full-file baseline.
  - Non-overlapping savings calculation (no double counting).
"""

import math
from typing import Dict, Any, Optional
from backend.config import settings

# Attempt to load tiktoken for cl100k_base (OpenAI/Gemini/modern LLM equivalent)
try:
    import tiktoken
    _enc = tiktoken.get_encoding("cl100k_base")
except Exception:
    _enc = None


def estimate_tokens(text: str) -> int:
    """
    Accurately estimate token count for code or prompt text.
    Uses tiktoken cl100k_base if available; falls back to 3.8 chars/token heuristic.
    """
    if not text:
        return 0
    if _enc is not None:
        try:
            return len(_enc.encode(text))
        except Exception:
            pass
    # Standard code token heuristic: ~3.8 characters per token in Python/JSON
    return max(1, math.ceil(len(text) / 3.8))


def calculate_full_file_baseline(source_code: str) -> Dict[str, int]:
    """
    Baseline definition:
    What would a naive AI-assisted development workflow cost if the entire source file
    and a verbose explanation request were sent to the AI model on every compile attempt?

    Baseline components:
      1. baseline_input: full_file_tokens + baseline_prompt_overhead (250 tokens)
      2. baseline_output: estimated response overhead (180 tokens or proportional to file size)
      3. baseline_total: baseline_input + baseline_output
    """
    file_tokens = estimate_tokens(source_code)
    prompt_overhead = settings.BASELINE_PROMPT_OVERHEAD_TOKENS
    output_expected = max(settings.BASELINE_EXPECTED_COMPLETION_TOKENS, file_tokens // 2)

    return {
        "full_file_tokens": file_tokens,
        "baseline_input": file_tokens + prompt_overhead,
        "baseline_output": output_expected,
        "baseline_total": file_tokens + prompt_overhead + output_expected,
    }


def compute_savings(
    source_code: str,
    resolution_source: str,  # "local", "cache", "ai", "mock"
    snippet_text: Optional[str] = None,
    prompt_sent: Optional[str] = None,
    actual_input_tokens: int = 0,
    actual_output_tokens: int = 0,
    is_mock: bool = False,
) -> Dict[str, Any]:
    """
    Compute actual usage vs full-file baseline and breakdown of tokens avoided.
    
    Non-overlapping savings categories:
      - avoided_by_local: AI call bypassed completely due to local compiler validation or local fix.
      - avoided_by_cache: AI call bypassed completely due to cache hit.
      - avoided_by_snippet: AI call was made, but only focused snippet was sent instead of full file.
    """
    baseline = calculate_full_file_baseline(source_code)
    baseline_total = baseline["baseline_total"]

    snippet_tokens = estimate_tokens(snippet_text or "")
    prompt_tokens_est = estimate_tokens(prompt_sent or "")

    avoided_by_local = 0
    avoided_by_cache = 0
    avoided_by_snippet = 0
    actual_total = actual_input_tokens + actual_output_tokens

    if resolution_source == "local":
        # 100% avoided locally
        avoided_by_local = baseline_total
        total_saved = avoided_by_local

    elif resolution_source == "cache":
        # 100% avoided via cache hit
        avoided_by_cache = baseline_total
        total_saved = avoided_by_cache

    elif resolution_source in ("ai", "mock"):
        # AI was called.
        # Savings come from sending only the snippet and compact prompt instead of full file.
        total_used = actual_total if actual_total > 0 else (prompt_tokens_est + settings.BASELINE_EXPECTED_COMPLETION_TOKENS)
        # Avoided = baseline_total - actual_used
        avoided_by_snippet = max(0, baseline_total - total_used)
        total_saved = avoided_by_snippet

    else:
        total_saved = 0

    # Percentage reduction vs baseline
    reduction_pct = 0.0
    if baseline_total > 0:
        reduction_pct = round((total_saved / baseline_total) * 100.0, 1)

    return {
        "baseline_tokens": baseline_total,
        "baseline_breakdown": baseline,
        "actual_input_tokens": actual_input_tokens,
        "actual_output_tokens": actual_output_tokens,
        "actual_total_tokens": actual_total,
        "is_mock": is_mock,
        "is_estimated": actual_total == 0 and resolution_source in ("ai", "mock"),
        "avoided_by_local": avoided_by_local,
        "avoided_by_cache": avoided_by_cache,
        "avoided_by_snippet": avoided_by_snippet,
        "total_tokens_saved": total_saved,
        "reduction_percentage": reduction_pct,
        "full_file_tokens_est": baseline["full_file_tokens"],
        "snippet_tokens_est": snippet_tokens,
    }
