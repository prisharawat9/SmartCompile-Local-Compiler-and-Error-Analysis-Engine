"""
Prompt Builder & Focused Snippet Extraction for SmartCompile.

Ensures minimal payload size by extracting only the relevant code section,
its immediate surrounding context, and diagnostic indicators, avoiding
the transmission of entire source files.
"""

from typing import Dict, Any, List, Optional, Tuple
from .token_accounting import estimate_tokens


def extract_focused_context(
    source_code: str,
    target_line: int = 1,
    context_lines: int = 3,
    provided_snippet: Optional[str] = None,
) -> Tuple[str, int, int]:
    """
    Extract a focused snippet around the diagnostic target line with line numbers.
    Returns: (snippet_text, start_line, end_line)
    """
    lines = source_code.splitlines()
    total_lines = len(lines)
    
    if total_lines == 0:
        return ("", 1, 1)

    target = max(1, min(total_lines, target_line))
    start_line = max(1, target - context_lines)
    end_line = min(total_lines, target + context_lines)

    numbered_lines = []
    for idx in range(start_line, end_line + 1):
        num = idx
        line_content = lines[idx - 1]
        marker = ">> " if num == target else "   "
        numbered_lines.append(f"{marker}{num:3d} | {line_content}")

    snippet_with_numbers = "\n".join(numbered_lines)
    return snippet_with_numbers, start_line, end_line


def build_focused_ai_payload(
    source_code: str,
    language: str,
    diagnostics: List[Dict[str, Any]],
    provided_snippet: Optional[str] = None,
    context_window: int = 3,
) -> Dict[str, Any]:
    """
    Construct the minimal, focused AI request payload and transparency metadata.
    """
    primary_diag = diagnostics[0] if diagnostics else {
        "line": 1,
        "column": 1,
        "message": "User requested AI code review or optimization.",
        "category": "ai-assisted",
    }

    target_line = primary_diag.get("line", 1)
    diag_msg = primary_diag.get("message", "Syntax or runtime error")
    diag_cat = primary_diag.get("category", "syntax")

    snippet_text, start_line, end_line = extract_focused_context(
        source_code, target_line, context_window, provided_snippet
    )

    system_prompt = (
        "You are SmartCompile AI, a high-efficiency compiler assistant. "
        "Analyze the provided code snippet and diagnostic. "
        "Respond in strict JSON with keys: "
        "'explanation' (1-2 sentences on root cause), "
        "'suggested_fix' (the exact replacement code for the erroneous line(s)), "
        "and 'corrected_snippet' (the complete corrected snippet without line number markers)."
    )

    user_prompt = (
        f"Language: {language}\n"
        f"Diagnostic: Line {target_line}: {diag_msg} (Category: {diag_cat})\n\n"
        f"Focused Code Snippet (Lines {start_line}-{end_line}):\n"
        f"```\n{snippet_text}\n```\n\n"
        "Provide a concise explanation and the minimal fix in JSON format."
    )

    full_char_count = len(source_code)
    snippet_char_count = len(snippet_text)
    combined_prompt = f"{system_prompt}\n\n{user_prompt}"
    prompt_tokens = estimate_tokens(combined_prompt)

    return {
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "combined_prompt": combined_prompt,
        "snippet_text": snippet_text,
        "line_start": start_line,
        "line_end": end_line,
        "target_line": target_line,
        "diagnostic_message": diag_msg,
        "diagnostic_category": diag_cat,
        "full_file_char_count": full_char_count,
        "snippet_char_count": snippet_char_count,
        "prompt_tokens_est": prompt_tokens,
    }
