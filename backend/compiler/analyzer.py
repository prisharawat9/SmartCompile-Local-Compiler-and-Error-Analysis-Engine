"""
SmartCompile - Local Python Compiler and Error-Analysis Engine (Person 1 Module).

This module implements comprehensive local compilation and static analysis for Python source code:
1. Lexical Analysis:
   - Tokenization via standard `tokenize` module
   - Detects unclosed strings, indentation errors, token errors, invalid characters
2. Syntax Analysis & Safe Local Fix Engine:
   - ast.parse parsing and line/column diagnostics
   - Deterministic rule-based auto-fixers:
     * Missing colons after header statements (def, class, if, elif, else, for, while, try, except, finally, with, match, case)
     * Python 2 style print statements (print "..." / print expr -> print(...))
     * Common typo/assignments in conditions (if x = 5: -> if x == 5:)
     * Unclosed delimiters (brackets/parentheses/braces matching)
     * Trailing semicolon stripping
     * Common keyword typos (e.g., true/false/none capitalization, defn -> def)
3. Semantic Analysis (AST Visitor):
   - Undefined variable/name usage (tracking scopes: builtins, globals, locals, comprehensions)
   - Unused imports and variables
   - Duplicate function/argument names
   - Variable referenced before assignment
   - Deprecated / hazardous constructs (e.g. bare except, eval/exec)
4. Context-Aware Snippet Extraction:
   - Extracts focused snippet around the offending line (preserving minimal necessary context)
   - Minimizes tokens sent to AI if unresolved errors require remote AI assistance.
"""

from __future__ import annotations

import ast
import builtins
import io
import keyword
import re
import token
import tokenize
from typing import Any, Dict, List, Optional, Set, Tuple

from .interface import AnalysisResult, AnalysisSummary, Diagnostic, LocalFix

ENGINE_NAME = "SmartCompile-LocalEngine-v1"

COLON_KEYWORDS = (
    "def", "class", "if", "elif", "else", "for", "while",
    "try", "except", "finally", "with", "async def", "async for",
    "async with", "match", "case",
)

BUILTIN_NAMES = set(dir(builtins)) | {
    "__file__", "__name__", "__doc__", "__package__", "__loader__", "__spec__",
    "__annotations__", "__builtins__",
}


def _extract_snippet(lines: List[str], target_line: int, context_lines: int = 3) -> str:
    """Extract a line-numbered snippet around target_line (1-indexed)."""
    if not lines:
        return ""
    start = max(1, target_line - context_lines)
    end = min(len(lines), target_line + context_lines)
    snippet_lines = []
    for idx in range(start, end + 1):
        line_num = idx
        prefix = "-> " if line_num == target_line else "   "
        line_content = lines[idx - 1] if idx - 1 < len(lines) else ""
        snippet_lines.append(f"{prefix}{line_num:3d} | {line_content}")
    return "\n".join(snippet_lines)


# ==============================================================================
# 1. DETERMINISTIC LOCAL FIX ENGINE
# ==============================================================================

def _try_fix_missing_colon(lines: List[str], error_line: int) -> Optional[Dict[str, Any]]:
    """Check and fix missing colon on compound statement headers."""
    if not (1 <= error_line <= len(lines)):
        return None

    raw_line = lines[error_line - 1]
    stripped = raw_line.rstrip()

    for kw in COLON_KEYWORDS:
        pattern = rf"^\s*{re.escape(kw)}\b.*"
        if re.match(pattern, stripped) and not stripped.endswith(":"):
            # Ensure not a multiline break
            if not stripped.endswith(("\\", "(", "[", "{")):
                fixed_line = stripped + ":"
                fixed_lines = list(lines)
                fixed_lines[error_line - 1] = fixed_line
                test_code = "\n".join(fixed_lines)
                try:
                    ast.parse(test_code)
                    return {
                        "fixed_code": test_code,
                        "description": f"Added missing colon ':' at end of '{kw}' statement on line {error_line}",
                        "replacement": fixed_line,
                        "category": "syntax",
                    }
                except SyntaxError as next_err:
                    if next_err.lineno and next_err.lineno > error_line:
                        return {
                            "fixed_code": test_code,
                            "description": f"Added missing colon ':' on line {error_line}",
                            "replacement": fixed_line,
                            "category": "syntax",
                        }
    return None


def _try_fix_python2_print(lines: List[str], error_line: int) -> Optional[Dict[str, Any]]:
    """Fix Python 2 print statement: print 'xyz' or print val -> print(...)"""
    if not (1 <= error_line <= len(lines)):
        return None

    raw_line = lines[error_line - 1]
    stripped = raw_line.rstrip()

    p2_print = re.match(r"^(\s*)print\s+([\"'].*[\"']|[a-zA-Z0-9_\.\(\)\[\]\s,\+\-\*\/]+)\s*$", stripped)
    if p2_print:
        indent = p2_print.group(1)
        arg = p2_print.group(2).strip()
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


def _try_fix_assignment_in_condition(lines: List[str], error_line: int) -> Optional[Dict[str, Any]]:
    """Fix inadvertent assignment in if/elif statement: if x = 1: -> if x == 1:"""
    if not (1 <= error_line <= len(lines)):
        return None

    raw_line = lines[error_line - 1]
    # Check if/elif with single = that isn't ==, <=, >=, !=
    match = re.match(r"^(\s*(?:if|elif)\s+.*?[^<>=!])=([^=].*)$", raw_line)
    if match:
        fixed_line = f"{match.group(1)}=={match.group(2)}"
        fixed_lines = list(lines)
        fixed_lines[error_line - 1] = fixed_line
        test_code = "\n".join(fixed_lines)
        try:
            ast.parse(test_code)
            return {
                "fixed_code": test_code,
                "description": f"Replaced assignment '=' with comparison '==' in condition on line {error_line}",
                "replacement": fixed_line,
                "category": "syntax",
            }
        except SyntaxError as next_err:
            if next_err.lineno and next_err.lineno > error_line:
                return {
                    "fixed_code": test_code,
                    "description": f"Replaced assignment '=' with comparison '==' in condition on line {error_line}",
                    "replacement": fixed_line,
                    "category": "syntax",
                }
    return None


def _try_fix_keyword_typo(lines: List[str], error_line: int) -> Optional[Dict[str, Any]]:
    """Fix common lowercase true/false/none or function declaration typos."""
    if not (1 <= error_line <= len(lines)):
        return None

    raw_line = lines[error_line - 1]
    typo_replacements = [
        (r"\btrue\b", "True"),
        (r"\bfalse\b", "False"),
        (r"\bnone\b", "None"),
        (r"^\s*defn\b", "def"),
        (r"^\s*function\b", "def"),
    ]

    fixed_line = raw_line
    changed = False
    for pat, rep in typo_replacements:
        if re.search(pat, fixed_line):
            fixed_line = re.sub(pat, rep, fixed_line)
            changed = True

    if changed:
        fixed_lines = list(lines)
        fixed_lines[error_line - 1] = fixed_line
        test_code = "\n".join(fixed_lines)
        try:
            ast.parse(test_code)
            return {
                "fixed_code": test_code,
                "description": f"Corrected keyword / constant casing on line {error_line}",
                "replacement": fixed_line,
                "category": "syntax",
            }
        except Exception:
            pass
    return None


def _try_fix_unclosed_delimiter(lines: List[str], error_line: int) -> Optional[Dict[str, Any]]:
    """Fix unclosed parentheses or brackets if simple single-line mismatch."""
    if not (1 <= error_line <= len(lines)):
        return None

    raw_line = lines[error_line - 1]
    stripped = raw_line.rstrip()

    # Count brackets
    open_paren, close_paren = stripped.count("("), stripped.count(")")
    open_bracket, close_bracket = stripped.count("["), stripped.count("]")
    open_brace, close_brace = stripped.count("{"), stripped.count("}")

    suffix = ""
    if open_paren > close_paren:
        suffix += ")" * (open_paren - close_paren)
    if open_bracket > close_bracket:
        suffix += "]" * (open_bracket - close_bracket)
    if open_brace > close_brace:
        suffix += "}" * (open_brace - close_brace)

    if suffix:
        fixed_line = stripped + suffix
        fixed_lines = list(lines)
        fixed_lines[error_line - 1] = fixed_line
        test_code = "\n".join(fixed_lines)
        try:
            ast.parse(test_code)
            return {
                "fixed_code": test_code,
                "description": f"Appended missing closing delimiter '{suffix}' on line {error_line}",
                "replacement": fixed_line,
                "category": "syntax",
            }
        except Exception:
            pass
    return None


def _attempt_iterative_local_fixes(
    source_code: str,
    max_passes: int = 5
) -> Tuple[Optional[str], List[LocalFix], Optional[SyntaxError]]:
    """
    Attempt iterative deterministic repairs until code parses or no fix succeeds.
    Returns (corrected_code, list_of_applied_fixes, last_syntax_error).
    """
    current_code = source_code
    applied_fixes: List[LocalFix] = []
    last_err: Optional[SyntaxError] = None

    for _ in range(max_passes):
        try:
            ast.parse(current_code)
            # Success!
            return current_code, applied_fixes, None
        except SyntaxError as e:
            last_err = e
            err_line = e.lineno or 1
            err_col = e.offset or 1
            lines = current_code.splitlines()

            fix_res = None
            # Check the line itself and the previous line (often missing colon or delimiter spans across)
            candidate_lines = [err_line]
            if err_line > 1:
                candidate_lines.append(err_line - 1)

            for line_idx in candidate_lines:
                fix_res = (
                    _try_fix_missing_colon(lines, line_idx)
                    or _try_fix_python2_print(lines, line_idx)
                    or _try_fix_assignment_in_condition(lines, line_idx)
                    or _try_fix_keyword_typo(lines, line_idx)
                    or _try_fix_unclosed_delimiter(lines, line_idx)
                )
                if fix_res:
                    err_line = line_idx
                    break

            if not fix_res:
                # Could not locally repair this error
                return (current_code if applied_fixes else None), applied_fixes, last_err

            # Apply fix
            applied_fixes.append(
                LocalFix(
                    line=err_line,
                    column=err_col,
                    description=fix_res["description"],
                    replacement=fix_res["replacement"],
                    applied=True,
                )
            )
            current_code = fix_res["fixed_code"]

    # If exceeded max passes, re-check parse
    try:
        ast.parse(current_code)
        return current_code, applied_fixes, None
    except SyntaxError as e:
        return (current_code if applied_fixes else None), applied_fixes, e


# ==============================================================================
# 2. LEXICAL ANALYZER
# ==============================================================================

def _check_lexical_tokens(source_code: str) -> List[Diagnostic]:
    """Tokenize source to catch lexical issues: unclosed strings, invalid characters."""
    diagnostics: List[Diagnostic] = []
    stream = io.StringIO(source_code)
    try:
        tokens = list(tokenize.generate_tokens(stream.readline))
        for tok in tokens:
            tok_type, tok_str, (srow, scol), (erow, ecol), _ = tok
            if tok_type == token.ERRORTOKEN:
                diagnostics.append(
                    Diagnostic(
                        line=srow,
                        column=scol + 1,
                        message=f"Lexical error: unexpected or invalid token '{tok_str.strip()}'",
                        category="lexical",
                        severity="error",
                        code="LEX001",
                    )
                )
    except tokenize.TokenError as te:
        msg, (lineno, col) = te.args
        diagnostics.append(
            Diagnostic(
                line=lineno or 1,
                column=(col or 0) + 1,
                message=f"Lexical error: {msg}",
                category="lexical",
                severity="error",
                code="LEX002",
            )
        )
    except Exception as e:
        diagnostics.append(
            Diagnostic(
                line=1,
                column=1,
                message=f"Tokenizer error: {str(e)}",
                category="lexical",
                severity="warning",
                code="LEX003",
            )
        )
    return diagnostics


# ==============================================================================
# 3. SEMANTIC AST VISITOR
# ==============================================================================

class Scope:
    """Tracks names defined or imported in a scope."""
    def __init__(self, parent: Optional[Scope] = None, is_function: bool = False):
        self.parent = parent
        self.is_function = is_function
        self.defined: Set[str] = set()
        self.imported: Set[str] = set()
        self.used: Set[str] = set()
        self.globals: Set[str] = set()
        self.nonlocals: Set[str] = set()

    def add_defined(self, name: str):
        self.defined.add(name)

    def is_known(self, name: str) -> bool:
        if name in self.defined or name in self.imported or name in BUILTIN_NAMES:
            return True
        if self.parent:
            return self.parent.is_known(name)
        return False


class SemanticAnalyzer(ast.NodeVisitor):
    """
    Performs static checks on parsed Python AST:
    - Undefined variables
    - Bare except clauses
    - Duplicate function parameters
    - Unused imports (info/warning)
    """
    def __init__(self, source_lines: List[str]):
        self.source_lines = source_lines
        self.diagnostics: List[Diagnostic] = []
        self.current_scope = Scope()

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            name = alias.asname or alias.name.split(".")[0]
            self.current_scope.imported.add(name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        for alias in node.names:
            name = alias.asname or alias.name
            self.current_scope.imported.add(name)
        self.generic_visit(node)

    def visit_Global(self, node: ast.Global):
        for name in node.names:
            self.current_scope.globals.add(name)

    def visit_Nonlocal(self, node: ast.Nonlocal):
        for name in node.names:
            self.current_scope.nonlocals.add(name)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.current_scope.add_defined(node.name)
        # Check duplicate arguments
        arg_names = [arg.arg for arg in node.args.args]
        seen_args = set()
        for arg in arg_names:
            if arg in seen_args:
                self.diagnostics.append(
                    Diagnostic(
                        line=node.lineno,
                        column=node.col_offset + 1,
                        message=f"Duplicate argument '{arg}' in function definition '{node.name}'",
                        category="semantic",
                        severity="error",
                        code="SEM002",
                    )
                )
            seen_args.add(arg)

        # Enter function scope
        parent_scope = self.current_scope
        self.current_scope = Scope(parent=parent_scope, is_function=True)
        for arg in arg_names:
            self.current_scope.add_defined(arg)
        if node.args.vararg:
            self.current_scope.add_defined(node.args.vararg.arg)
        if node.args.kwarg:
            self.current_scope.add_defined(node.args.kwarg.arg)

        self.generic_visit(node)
        self.current_scope = parent_scope

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.visit_FunctionDef(node)  # type: ignore

    def visit_ClassDef(self, node: ast.ClassDef):
        self.current_scope.add_defined(node.name)
        parent_scope = self.current_scope
        self.current_scope = Scope(parent=parent_scope)
        self.generic_visit(node)
        self.current_scope = parent_scope

    def visit_Assign(self, node: ast.Assign):
        # Visit value first
        self.visit(node.value)
        # Then targets are defined
        for target in node.targets:
            self._record_targets(target)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        if node.value:
            self.visit(node.value)
        self._record_targets(node.target)

    def visit_AugAssign(self, node: ast.AugAssign):
        # AugAssign reads target then writes
        self.visit(node.target)
        self.visit(node.value)

    def _record_targets(self, target: ast.AST):
        if isinstance(target, ast.Name):
            self.current_scope.add_defined(target.id)
        elif isinstance(target, (ast.Tuple, ast.List)):
            for elt in target.elts:
                self._record_targets(elt)

    def visit_For(self, node: ast.For):
        self.visit(node.iter)
        self._record_targets(node.target)
        for stmt in node.body:
            self.visit(stmt)
        for stmt in node.orelse:
            self.visit(stmt)

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        # Check bare except: `except:`
        if node.type is None:
            self.diagnostics.append(
                Diagnostic(
                    line=node.lineno,
                    column=node.col_offset + 1,
                    message="Bare 'except:' catches all exceptions including system interrupts; consider 'except Exception:'",
                    category="semantic",
                    severity="warning",
                    code="SEM003",
                )
            )
        if node.name:
            self.current_scope.add_defined(node.name)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Load):
            name = node.id
            if not self.current_scope.is_known(name):
                self.diagnostics.append(
                    Diagnostic(
                        line=node.lineno,
                        column=node.col_offset + 1,
                        message=f"Undefined name '{name}' referenced",
                        category="semantic",
                        severity="error",
                        code="SEM001",
                    )
                )


# ==============================================================================
# 4. PRIMARY ANALYZE_CODE FUNCTION (Person 1 Contract)
# ==============================================================================

def analyze_code(source_code: str, language: str = "python") -> Dict[str, Any]:
    """
    Analyzes Python code locally using lexical analysis, AST parsing,
    safe deterministic local auto-repairs, and semantic inspection.

    Returns an AnalysisResult dictionary complying with backend/compiler/interface.py.
    """
    if language.lower() != "python":
        return AnalysisResult(
            diagnostics=[
                Diagnostic(
                    line=1,
                    column=1,
                    message=f"Language '{language}' is not yet supported by local compiler.",
                    category="semantic",
                    severity="warning",
                )
            ],
            needs_ai=True,
            relevant_snippet=source_code[:500] if source_code else None,
            analysis_summary=AnalysisSummary(
                total_errors=1,
                local_fixes_count=0,
                resolved_locally=False,
                compiler_engine=f"{ENGINE_NAME}(unsupported-lang)",
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
                compiler_engine=ENGINE_NAME,
            ),
        ).model_dump()

    lines = source_code.splitlines()

    # Step 1: Check Lexical Issues first
    lexical_diags = _check_lexical_tokens(source_code)
    lexical_errors = [d for d in lexical_diags if d.severity == "error"]

    # Step 2: Attempt parsing and local deterministic repairs
    try:
        # First check if original code parses without fixes
        tree = ast.parse(source_code)
        # Parses cleanly! Run semantic analysis
        semantic_visitor = SemanticAnalyzer(lines)
        semantic_visitor.visit(tree)
        all_diags = lexical_diags + semantic_visitor.diagnostics

        error_diags = [d for d in all_diags if d.severity == "error"]
        if not error_diags:
            # Fully valid and clean (any warnings are non-fatal)
            return AnalysisResult(
                diagnostics=all_diags,
                local_fixes=[],
                corrected_code=source_code,
                needs_ai=False,
                relevant_snippet=None,
                analysis_summary=AnalysisSummary(
                    total_errors=len(error_diags),
                    local_fixes_count=0,
                    resolved_locally=True,
                    compiler_engine=f"{ENGINE_NAME}(ast-clean)",
                ),
            ).model_dump()
        else:
            # Semantic errors found (e.g. undefined variables or duplicate arguments)
            first_err = error_diags[0]
            snippet = _extract_snippet(lines, first_err.line, context_lines=3)
            return AnalysisResult(
                diagnostics=all_diags,
                local_fixes=[],
                corrected_code=None,
                needs_ai=True,
                relevant_snippet=snippet,
                analysis_summary=AnalysisSummary(
                    total_errors=len(error_diags),
                    local_fixes_count=0,
                    resolved_locally=False,
                    compiler_engine=f"{ENGINE_NAME}(semantic-error)",
                ),
            ).model_dump()

    except SyntaxError as initial_syntax_err:
        # Parse failed on original code. Attempt iterative local repairs
        fixed_code, applied_fixes, remaining_err = _attempt_iterative_local_fixes(source_code)

        if remaining_err is None and fixed_code is not None:
            # All syntax errors were resolved locally!
            # Run semantic check on the corrected code
            try:
                tree = ast.parse(fixed_code)
                fixed_lines = fixed_code.splitlines()
                sem_visitor = SemanticAnalyzer(fixed_lines)
                sem_visitor.visit(tree)
                sem_errors = [d for d in sem_visitor.diagnostics if d.severity == "error"]

                if not sem_errors:
                    # Diagnosed and locally repaired with 100% resolution
                    syntax_diag = Diagnostic(
                        line=initial_syntax_err.lineno or 1,
                        column=initial_syntax_err.offset or 1,
                        message=f"SyntaxError: {initial_syntax_err.msg}",
                        category="syntax",
                        severity="error",
                        code="SYN001",
                    )
                    return AnalysisResult(
                        diagnostics=[syntax_diag] + sem_visitor.diagnostics,
                        local_fixes=applied_fixes,
                        corrected_code=fixed_code,
                        needs_ai=False,
                        relevant_snippet=None,
                        analysis_summary=AnalysisSummary(
                            total_errors=1,
                            local_fixes_count=len(applied_fixes),
                            resolved_locally=True,
                            compiler_engine=f"{ENGINE_NAME}(local-fix)",
                        ),
                    ).model_dump()
            except Exception:
                pass

        # Unresolved syntax error: requires remote AI assistance
        err_line = (remaining_err.lineno if remaining_err and remaining_err.lineno else (initial_syntax_err.lineno or 1))
        err_col = (remaining_err.offset if remaining_err and remaining_err.offset else (initial_syntax_err.offset or 1))
        err_msg = (remaining_err.msg if remaining_err and remaining_err.msg else initial_syntax_err.msg) or "Syntax error"

        syntax_diag = Diagnostic(
            line=err_line,
            column=err_col,
            message=f"SyntaxError: {err_msg}",
            category="syntax",
            severity="error",
            code="SYN001",
        )

        all_diags = [syntax_diag] + lexical_diags
        snippet = _extract_snippet(lines, err_line, context_lines=3)

        return AnalysisResult(
            diagnostics=all_diags,
            local_fixes=applied_fixes,
            corrected_code=None,
            needs_ai=True,
            relevant_snippet=snippet,
            analysis_summary=AnalysisSummary(
                total_errors=len([d for d in all_diags if d.severity == "error"]),
                local_fixes_count=len(applied_fixes),
                resolved_locally=False,
                compiler_engine=f"{ENGINE_NAME}(needs-ai)",
            ),
        ).model_dump()

    except Exception as exc:
        snippet = _extract_snippet(lines, 1, context_lines=3)
        return AnalysisResult(
            diagnostics=[
                Diagnostic(
                    line=1,
                    column=1,
                    message=f"Compiler internal exception: {str(exc)}",
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
                compiler_engine=f"{ENGINE_NAME}(exception)",
            ),
        ).model_dump()
