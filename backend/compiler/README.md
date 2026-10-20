# Compiler Engine Integration Guide (Person 1 Module)

Welcome, Person 1! This folder hosts your Python local compiler and error-analysis engine.

## Your Target File
Place your implementation in:
```
backend/compiler/analyzer.py
```

## Required Signature
Your module MUST export:
```python
def analyze_code(source_code: str, language: str = "python") -> dict:
    ...
```

## Expected Return Dictionary Format
Your output dictionary should conform to `backend/compiler/interface.py`:
```json
{
  "diagnostics": [
    {
      "line": 12,
      "column": 5,
      "message": "SyntaxError: invalid syntax",
      "category": "syntax",
      "severity": "error",
      "code": "SYN001"
    }
  ],
  "local_fixes": [
    {
      "line": 12,
      "column": 5,
      "description": "Added missing colon at end of statement",
      "replacement": "def calculate_sum(a, b):",
      "applied": true
    }
  ],
  "corrected_code": "def calculate_sum(a, b):\n    return a + b\n",
  "needs_ai": false,
  "relevant_snippet": null,
  "analysis_summary": {
    "total_errors": 1,
    "local_fixes_count": 1,
    "resolved_locally": true,
    "compiler_engine": "Person1-CompilerEngine"
  }
}
```

## How the Rest of SmartCompile Integrates With You
- `backend/compiler/loader.py` will automatically detect `analyzer.py` once created.
- Until then, the system falls back to `backend/compiler/analyzer_stub.py` without breaking any other module.
- The analysis endpoint `POST /api/analyze` forwards directly to your `analyze_code`.
- The compilation router `POST /api/compile` will:
  1. Call your `analyze_code`.
  2. If `needs_ai == false`, immediately return local results and save 100% of AI tokens!
  3. If `needs_ai == true`, route **only** your `relevant_snippet` (not the whole file) to cache/AI.
