"""
Persistent SQLite Cache Service for SmartCompile.

Provides deterministic caching of AI responses to prevent redundant API calls.
Cache keys are formed via SHA-256 over normalized code snippet, diagnostic context,
language, provider, and model.
"""

from datetime import datetime, timezone
import hashlib
import json
import logging
import re
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from backend.db.database import get_db_connection

logger = logging.getLogger("smartcompile.cache")


class CachedResponse(BaseModel):
    cache_key: str
    explanation: str
    suggested_fix: str
    tokens_input: int = 0
    tokens_output: int = 0
    provider: str
    model: str
    is_mock: bool = False
    hit_count: int = 0
    created_at: str
    last_accessed_at: str
    cache_hit_reason: str = Field(default="Exact match on normalized snippet and diagnostic context")


import textwrap


def normalize_code_snippet(snippet: str) -> str:
    """
    Normalize snippet to ensure stable hashing:
    - Normalizes line endings to \n
    - Strips line number prefixes (e.g. '>> 12 | ')
    - Dedents uniform indentation
    - Trims trailing spaces per line
    - Trims leading and trailing blank lines
    """
    if not snippet:
        return ""
    # Strip line numbering prefixes if present
    cleaned = re.sub(r"^(>>|\s{2})\s*\d+\s*\|\s*", "", snippet, flags=re.MULTILINE)
    dedented = textwrap.dedent(cleaned)
    lines = [line.rstrip() for line in dedented.splitlines()]
    # Remove leading/trailing empty lines
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)


def generate_cache_key(
    snippet: str,
    diagnostic_msg: str,
    category: str,
    language: str,
    model: str,
    provider: str,
) -> str:
    """Generate deterministic SHA-256 cache key."""
    norm_snippet = normalize_code_snippet(snippet)
    norm_diag = diagnostic_msg.strip().lower()
    norm_cat = category.strip().lower()
    norm_lang = language.strip().lower()
    norm_model = model.strip().lower()
    norm_provider = provider.strip().lower()

    raw_signature = f"{norm_lang}|{norm_provider}|{norm_model}|{norm_cat}|{norm_diag}|{norm_snippet}"
    return hashlib.sha256(raw_signature.encode("utf-8")).hexdigest()


class CacheService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def get(self, cache_key: str) -> Optional[CachedResponse]:
        """Retrieve entry if present; increment hit count and log event."""
        conn = get_db_connection(self.db_path)
        try:
            row = conn.execute(
                "SELECT * FROM ai_cache WHERE cache_key = ?", (cache_key,)
            ).fetchone()

            now_iso = datetime.now(timezone.utc).isoformat()

            if row:
                new_hit_count = row["hit_count"] + 1
                with conn:
                    conn.execute(
                        "UPDATE ai_cache SET hit_count = ?, last_accessed_at = ? WHERE cache_key = ?",
                        (new_hit_count, now_iso, cache_key),
                    )
                    conn.execute(
                        "INSERT INTO cache_events (timestamp, cache_key, event_type, provider, model) VALUES (?, ?, 'hit', ?, ?)",
                        (now_iso, cache_key, row["provider"], row["model"]),
                    )

                return CachedResponse(
                    cache_key=row["cache_key"],
                    explanation=row["response_explanation"],
                    suggested_fix=row["response_fix"],
                    tokens_input=row["tokens_input"],
                    tokens_output=row["tokens_output"],
                    provider=row["provider"],
                    model=row["model"],
                    is_mock=bool(row["is_mock"]),
                    hit_count=new_hit_count,
                    created_at=row["created_at"],
                    last_accessed_at=now_iso,
                    cache_hit_reason=f"Hit on cache key ({row['hit_count']} previous hits). Cached at {row['created_at']}.",
                )

            # Record cache miss
            with conn:
                conn.execute(
                    "INSERT INTO cache_events (timestamp, cache_key, event_type) VALUES (?, ?, 'miss')",
                    (now_iso, cache_key),
                )
            return None
        finally:
            conn.close()

    def set(
        self,
        cache_key: str,
        snippet: str,
        diagnostic_msg: str,
        language: str,
        model: str,
        provider: str,
        prompt_sent: str,
        response_explanation: str,
        response_fix: str,
        tokens_input: int = 0,
        tokens_output: int = 0,
        is_mock: bool = False,
    ) -> None:
        """Store or update cache record."""
        now_iso = datetime.now(timezone.utc).isoformat()
        snippet_hash = hashlib.sha256(normalize_code_snippet(snippet).encode()).hexdigest()
        diag_hash = hashlib.sha256(diagnostic_msg.encode()).hexdigest()

        conn = get_db_connection(self.db_path)
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO ai_cache (
                        cache_key, snippet_hash, diagnostic_hash, language, model, provider,
                        prompt_sent, response_explanation, response_fix, tokens_input,
                        tokens_output, is_mock, created_at, last_accessed_at, hit_count
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                    ON CONFLICT(cache_key) DO UPDATE SET
                        response_explanation = excluded.response_explanation,
                        response_fix = excluded.response_fix,
                        tokens_input = excluded.tokens_input,
                        tokens_output = excluded.tokens_output,
                        last_accessed_at = excluded.last_accessed_at;
                    """,
                    (
                        cache_key,
                        snippet_hash,
                        diag_hash,
                        language,
                        model,
                        provider,
                        prompt_sent,
                        response_explanation,
                        response_fix,
                        tokens_input,
                        tokens_output,
                        1 if is_mock else 0,
                        now_iso,
                        now_iso,
                    ),
                )
                conn.execute(
                    "INSERT INTO cache_events (timestamp, cache_key, event_type, provider, model) VALUES (?, ?, 'set', ?, ?)",
                    (now_iso, cache_key, provider, model),
                )
        finally:
            conn.close()

    def get_stats(self) -> Dict[str, Any]:
        """Aggregate cache statistics."""
        conn = get_db_connection(self.db_path)
        try:
            entry_count = conn.execute("SELECT COUNT(*) as c FROM ai_cache").fetchone()["c"]
            hits_from_events = conn.execute(
                "SELECT COUNT(*) as c FROM cache_events WHERE event_type = 'hit'"
            ).fetchone()["c"]
            misses_from_events = conn.execute(
                "SELECT COUNT(*) as c FROM cache_events WHERE event_type = 'miss'"
            ).fetchone()["c"]

            total_accesses = hits_from_events + misses_from_events
            hit_rate = round((hits_from_events / total_accesses * 100), 1) if total_accesses > 0 else 0.0

            return {
                "total_entries": entry_count,
                "total_hits": hits_from_events,
                "total_misses": misses_from_events,
                "total_lookups": total_accesses,
                "hit_rate_percentage": hit_rate,
            }
        finally:
            conn.close()

    def clear(self) -> Dict[str, Any]:
        """Delete all cached entries."""
        conn = get_db_connection(self.db_path)
        try:
            now_iso = datetime.now(timezone.utc).isoformat()
            with conn:
                count = conn.execute("SELECT COUNT(*) as c FROM ai_cache").fetchone()["c"]
                conn.execute("DELETE FROM ai_cache")
                conn.execute(
                    "INSERT INTO cache_events (timestamp, event_type) VALUES (?, 'clear')",
                    (now_iso,),
                )
            return {"status": "success", "cleared_entries": count}
        finally:
            conn.close()


# Global cache service instance
cache_service = CacheService()
