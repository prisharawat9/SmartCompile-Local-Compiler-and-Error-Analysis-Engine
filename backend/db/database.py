"""
SQLite Database Layer for SmartCompile.
Manages persistent cache, compilation history, and analytics records.
"""

import sqlite3
import json
import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from backend.config import settings

logger = logging.getLogger("smartcompile.db")


def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Create and configure a SQLite connection."""
    path = db_path or settings.DATABASE_PATH
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Enable WAL mode for better concurrency and foreign keys
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
    except Exception as e:
        logger.debug(f"SQLite PRAGMA setting note: {e}")
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """Initialize SQLite database tables and indexes."""
    conn = get_db_connection(db_path)
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ai_cache (
                cache_key TEXT PRIMARY KEY,
                snippet_hash TEXT NOT NULL,
                diagnostic_hash TEXT NOT NULL,
                language TEXT NOT NULL,
                model TEXT NOT NULL,
                provider TEXT NOT NULL,
                prompt_sent TEXT NOT NULL,
                response_explanation TEXT NOT NULL,
                response_fix TEXT NOT NULL,
                tokens_input INTEGER DEFAULT 0,
                tokens_output INTEGER DEFAULT 0,
                is_mock INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                last_accessed_at TEXT NOT NULL,
                hit_count INTEGER DEFAULT 0
            );
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_ai_cache_snippet 
            ON ai_cache(snippet_hash, language, model);
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS compilation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                language TEXT NOT NULL,
                source_code TEXT NOT NULL,
                full_code_tokens_est INTEGER NOT NULL,
                snippet_tokens_est INTEGER DEFAULT 0,
                diagnostics_json TEXT NOT NULL,
                local_fixes_json TEXT NOT NULL,
                status TEXT NOT NULL,
                resolution_source TEXT NOT NULL,
                ai_provider TEXT,
                ai_model TEXT,
                actual_input_tokens INTEGER DEFAULT 0,
                actual_output_tokens INTEGER DEFAULT 0,
                estimated_input_tokens INTEGER DEFAULT 0,
                estimated_output_tokens INTEGER DEFAULT 0,
                estimated_tokens_saved INTEGER DEFAULT 0,
                baseline_tokens INTEGER DEFAULT 0,
                explanation TEXT,
                corrected_code TEXT,
                request_payload_json TEXT,
                error_message TEXT
            );
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_history_timestamp 
            ON compilation_history(timestamp DESC);
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_history_source 
            ON compilation_history(resolution_source);
        """)

        # Cache events log for accurate hit/miss/clear auditing
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cache_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                cache_key TEXT,
                event_type TEXT NOT NULL, -- 'hit', 'miss', 'set', 'clear'
                provider TEXT,
                model TEXT
            );
        """)
    conn.close()
    logger.info(f"Database initialized at {db_path or settings.DATABASE_PATH}")
