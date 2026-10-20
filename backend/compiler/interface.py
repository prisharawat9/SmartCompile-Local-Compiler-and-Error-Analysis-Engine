"""
Compiler Integration Interface for SmartCompile.

This module defines the contract and data structures agreed upon between:
- Person 1: Compiler & Error-Analysis Engine (backend/compiler/analyzer.py)
- Person 2: AI Routing, Caching, Token Accounting & Dashboard

Person 1 is expected to implement:
    analyze_code(source_code: str, language: str = "python") -> dict

Output format:
{
    "diagnostics": [
        {
            "line": int,              # 1-indexed
            "column": int,            # 1-indexed (optional, default 1)
            "message": str,           # Descriptive error/warning message
            "category": str,          # "lexical", "syntax", "semantic", "runtime"
            "severity": str,          # "error", "warning", "info"
            "code": str | None        # Optional rule or error code (e.g., "E999")
        }
    ],
    "local_fixes": [
        {
            "line": int,
            "column": int,
            "description": str,       # Explanation of the local fix
            "replacement": str,       # The corrected line or snippet
            "applied": bool           # True if automatically applied to corrected_code
        }
    ],
    "corrected_code": str | None,     # Source code with safe local fixes applied, or None
    "needs_ai": bool,                 # True if there are unresolved issues requiring AI
    "relevant_snippet": str | None,   # Focused code section to send to AI (NOT the entire file)
    "analysis_summary": {
        "total_errors": int,
        "local_fixes_count": int,
        "resolved_locally": bool,
        "compiler_engine": str        # Name of compiler/analyzer engine used
    }
}
"""

from typing import List, Optional, Literal, TypedDict, Dict, Any
from pydantic import BaseModel, Field


class Diagnostic(BaseModel):
    line: int = Field(..., ge=1, description="1-indexed line number")
    column: int = Field(default=1, ge=1, description="1-indexed column number")
    message: str = Field(..., description="Description of the diagnostic")
    category: Literal["lexical", "syntax", "semantic", "runtime", "ai-assisted"] = Field(
        default="syntax", description="Category of the error"
    )
    severity: Literal["error", "warning", "info"] = Field(
        default="error", description="Severity level"
    )
    code: Optional[str] = Field(default=None, description="Error identifier/rule code")


class LocalFix(BaseModel):
    line: int = Field(..., ge=1, description="1-indexed line number")
    column: int = Field(default=1, ge=1, description="1-indexed column number")
    description: str = Field(..., description="Explanation of what was fixed")
    replacement: str = Field(..., description="Proposed replacement text/line")
    applied: bool = Field(default=True, description="Whether fix was applied to corrected_code")


class AnalysisSummary(BaseModel):
    total_errors: int = Field(default=0)
    local_fixes_count: int = Field(default=0)
    resolved_locally: bool = Field(default=True)
    compiler_engine: str = Field(default="SmartCompile-Engine")


class AnalysisResult(BaseModel):
    diagnostics: List[Diagnostic] = Field(default_factory=list)
    local_fixes: List[LocalFix] = Field(default_factory=list)
    corrected_code: Optional[str] = Field(default=None)
    needs_ai: bool = Field(default=False)
    relevant_snippet: Optional[str] = Field(default=None)
    analysis_summary: AnalysisSummary = Field(default_factory=AnalysisSummary)
