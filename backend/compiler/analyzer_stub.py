"""
Development stub for Person 1's Compiler & Error-Analysis Engine.

This stub provides realistic local analysis while Person 1 develops backend/compiler/analyzer.py.
It implements:
  - ast.parse validation for Python
  - Local heuristic fixes for common syntax errors (missing colons, Python 2 print syntax)
  - Identification of unresolved errors that require AI assistance
  - Extraction of focused, relevant code snippets (avoiding full-file submission)

When Person 1 implements backend/compiler/analyzer.py, the loader automatically prefers it.
"""

import ast
import re
from typing import Dict, Any, List, Optional
from .interface import Diagnostic, LocalFix, AnalysisSummary, AnalysisResult


COLON_KEYWORDS = ("def", "class", "if", "elif", "else", "for", "while", "try", "except", "finally", "with")


def _extract_snippet(lines: List[str], target_line: int, context_lines: int = 3) -> str:
    """Extract snippet around target line (1-indexed)."""
    start = max(1, target_line - context_lines)
    end = min(len(lines), target_line + context_lines)
    snippet_lines = []
    for idx in range(start, end + 1):
        line_num = idx
        prefix = "-> " if line_num == target_line else "   "
        snippet_lines.append(f"{prefix}{line_num:3d} | {lines[idx - 1]}")
    return "\n".join(snippet_lines)


def _try_local_fixes(source_code: str, error_line: int, error_msg: str) -> Optional[Dict[str, Any]]:
    """
    Attempt safe local deterministic fixes for common Python errors:
    1. Missing colon after def/if/for/while/class etc.
    2. Python 2 print "string" -> print("string")
    3. Trailing comma/whitespace issues
    """
    lines = source_code.splitlines()
    if not (1 <= error_line <= len(lines)):
        return None

    raw_line = lines[error_line - 1]
    stripped = raw_line.rstrip()

    # 1. Missing colon check
    for kw in COLON_KEYWORDS:
        # Check if line begins with keyword (handling indentation)
        pattern = rf"^\s*{kw}\b.*"
        if re.match(pattern, stripped) and not stripped.endswith(":"):
            # Check if this might be a multiline statement where colon comes later
            if not stripped.endswith(("\\", "(", "[", "{")):
                fixed_line = stripped + ":"
                fixed_lines = list(lines)
                fixed_lines[error_line - 1] = fixed_line
                test_code = "\n".join(fixed_lines)
                # Verify if test_code fixes or parses
                try:
                    ast.parse(test_code)
                    return {
                        "fixed_code": test_code,
                        "description": f"Added missing colon ':' at end of '{kw}' statement on line {error_line}",
                        "replacement": fixed_line,
                        "category": "syntax",
                    }
                except SyntaxError as next_err:
                    # Even if there's another error further down, if this error moved past error_line, it helped
                    if next_err.lineno and next_err.lineno > error_line:
                        return {
                            "fixed_code": test_code,
                            "description": f"Added missing colon ':' on line {error_line}",
                            "replacement": fixed_line,
                            "category": "syntax",
                        }

    # 2. Python 2 print statement: print "hello" or print 'hello' or print x
    p2_print = re.match(r"^(\s*)print\s+([\"'].*[\"']|[a-zA-Z0-9_]+)\s*$", stripped)
    if p2_print:
        indent = p2_print.group(1)
        arg = p2_print.group(2)
        fixed_line = f"{indent}print({arg})"
        fixed_lines = list(lines)
        fixed_lines[error_line - 1] = fixed_line
        test_code = "\n".join(fixed_lines)
        try:
            ast.parse(test_code)
            return {
                "fixed_code": test_code,
                "description": f"Converted Python 2 print statement to Python 3 function call print(...) on line {error_line}",
                "replacement": fixed_line,
                "category": "syntax",
            }
        except Exception:
            pass

    return None


def analyze_code_stub(source_code: str, language: str = "python") -> Dict[str, Any]:
    """
    Local compiler analysis stub.
    Implements analyze_code(source_code, language) -> dict.
    """
    if language.lower() != "python":
        return AnalysisResult(
            diagnostics=[
                Diagnostic(
                    line=1,
                    column=1,
                    message=f"Language '{language}' local compiler not supported yet.",
                    category="semantic",
                    severity="warning",
                )
            ],
            needs_ai=True,
            relevant_snippet=source_code[:500],
            analysis_summary=AnalysisSummary(
                total_errors=1,
                local_fixes_count=0,
                resolved_locally=False,
                compiler_engine="StubCompilerEngine(unsupported-lang)",
            ),
        ).model_dump()

    # Empty code check
    if not source_code.strip():
        return AnalysisResult(
            diagnostics=[],
            local_fixes=[],
            corrected_code=source_code,
            needs_ai=False,
            relevant_snippet=None,
            analysis_summary=AnalysisSummary(
                total_errors=0,
                local_fixes_count=0,
                resolved_locally=True,
                compiler_engine="StubCompilerEngine",
            ),
        ).model_dump()

    lines = source_code.splitlines()

    # Step 1: Attempt Python ast.parse to find syntax/lexical errors
    try:
        tree = ast.parse(source_code)
        # Check for semantic warnings / undefined basic checks or known error comments
        # If code parses cleanly without syntax errors:
        return AnalysisResult(
            diagnostics=[],
            local_fixes=[],
            corrected_code=source_code,
            needs_ai=False,
            relevant_snippet=None,
            analysis_summary=AnalysisSummary(
                total_errors=0,
                local_fixes_count=0,
                resolved_locally=True,
                compiler_engine="StubCompilerEngine(ast-clean)",
            ),
        ).model_dump()

    except SyntaxError as e:
        err_line = e.lineno or 1
        err_col = e.offset or 1
        err_msg = e.msg or "Syntax error detected"

        diag = Diagnostic(
            line=err_line,
            column=err_col,
            message=f"SyntaxError: {err_msg}",
            category="syntax",
            severity="error",
            code="SYN001",
        )

        # Attempt local fix
        fix_attempt = _try_local_fixes(source_code, err_line, err_msg)
        if fix_attempt:
            local_fix = LocalFix(
                line=err_line,
                column=err_col,
                description=fix_attempt["description"],
                replacement=fix_attempt["replacement"],
                applied=True,
            )
            return AnalysisResult(
                diagnostics=[diag],
                local_fixes=[local_fix],
                corrected_code=fix_attempt["fixed_code"],
                needs_ai=False,  # Successfully resolved locally without AI!
                relevant_snippet=None,
                analysis_summary=AnalysisSummary(
                    total_errors=1,
                    local_fixes_count=1,
                    resolved_locally=True,
                    compiler_engine="StubCompilerEngine(local-fix)",
                ),
            ).model_dump()

        # Unresolved error: Needs AI assistance
        snippet = _extract_snippet(lines, err_line, context_lines=3)
        return AnalysisResult(
            diagnostics=[diag],
            local_fixes=[],
            corrected_code=None,
            needs_ai=True,  # Requires AI to analyze and fix
            relevant_snippet=snippet,
            analysis_summary=AnalysisSummary(
                total_errors=1,
                local_fixes_count=0,
                resolved_locally=False,
                compiler_engine="StubCompilerEngine(needs-ai)",
            ),
        ).model_dump()

    except Exception as general_err:
        snippet = _extract_snippet(lines, 1, context_lines=3)
        return AnalysisResult(
            diagnostics=[
                Diagnostic(
                    line=1,
                    column=1,
                    message=f"Analysis error: {str(general_err)}",
                    category="runtime",
                    severity="error",
                )
            ],
            local_fixes=[],
            corrected_code=None,
            needs_ai=True,
            relevant_snippet=snippet,
            analysis_summary=AnalysisSummary(
                total_errors=1,
                local_fixes_count=0,
                resolved_locally=False,
                compiler_engine="StubCompilerEngine(exception)",
            ),
        ).model_dump()
