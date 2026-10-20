# SmartCompile — AI Optimization, Compiler Routing, Caching & Analytics Dashboard

SmartCompile is a high-efficiency developer platform that reduces AI API costs and token consumption by analyzing code locally first and transmitting **only unresolved, relevant code sections** to an AI provider.

This repository implements **Person 2's module** (AI Routing, SQLite Persistent Caching, Token Accounting, Recharts/Monaco Dashboard, and Full Application Integration), with a clean drop-in interface for **Person 1's local Python compiler engine**.

---

## Architecture Overview

```
                      +-----------------------------+
                      | React Dashboard (Vite + TS) |
                      | Monaco Editor + Recharts    |
                      +--------------+--------------+
                                     |  HTTP REST
                                     v
                      +-----------------------------+
                      |   FastAPI Backend (Port 8000)|
                      +--------------+--------------+
                                     |
               +---------------------+---------------------+
               |                                           |
               v                                           v
+-------------------------------+           +-------------------------------+
|  Local Compiler Analysis      |           |  Intelligent AI Routing       |
|  - Person 1: analyzer.py      |           |  - Token baseline comparison  |
|  - Fallback: analyzer_stub.py |           |  - Partial snippet extraction |
+--------------+----------------+           +---------------+---------------+
               |                                            |
       [All Resolved / Clean]                               | [Unresolved Bug]
               |                                            v
               |                             +-------------------------------+
               +---------------------------->| Persistent SQLite Cache       |
               |                             | - Deterministic SHA-256 keys  |
               |                             | - Instant 0-token reuse       |
               |                             +--------------+----------------+
               |                                            | [Cache Miss]
               |                                            v
               |                             +-------------------------------+
               |                             | Configurable AI Provider      |
               |                             | - Mock (simulated for demo)   |
               |                             | - OpenAI / Gemini / Claude    |
               |                             +-------------------------------+
               v
+-------------------------------+
| Telemetry & SQLite Audit Log  |
| (Compilations, Tokens, Cache) |
+-------------------------------+
```

---

## 1. Quick Start Guide

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm

### A. Backend Setup
```bash
# 1. Activate Python virtual environment
source venv/bin/activate

# 2. Install dependencies (if not already installed)
pip install -r requirements.txt

# 3. Start the FastAPI backend server
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
The backend will be available at: **http://127.0.0.1:8000**
Interactive API Swagger Docs: **http://127.0.0.1:8000/docs**

### B. Frontend Setup
```bash
# 1. Navigate into frontend directory
cd frontend

# 2. Start Vite development server
npm run dev
```
The React Monaco dashboard will be live at: **http://127.0.0.1:5173**

---

## 2. Person 1 Integration Interface

Person 1 implements the local compiler engine in:
```
backend/compiler/analyzer.py
```

### Required Function Signature
```python
def analyze_code(source_code: str, language: str = "python") -> dict:
    ...
```

### Return Contract
```json
{
  "diagnostics": [
    {
      "line": 10,
      "column": 4,
      "message": "SyntaxError: expected ':'",
      "category": "syntax",
      "severity": "error",
      "code": "SYN001"
    }
  ],
  "local_fixes": [
    {
      "line": 10,
      "column": 4,
      "description": "Added missing colon ':' on line 10",
      "replacement": "if condition:",
      "applied": true
    }
  ],
  "corrected_code": "def example():\n    if condition:\n        pass\n",
  "needs_ai": false,
  "relevant_snippet": null,
  "analysis_summary": {
    "total_errors": 1,
    "local_fixes_count": 1,
    "resolved_locally": true,
    "compiler_engine": "MyCompilerEngine"
  }
}
```

> **Note:** Until Person 1 provides `analyzer.py`, `backend/compiler/loader.py` automatically utilizes the realistic `backend/compiler/analyzer_stub.py` (which uses AST parsing and regex heuristic fixers). Once `analyzer.py` is created, it is imported automatically without any code changes!

---

## 3. How AI Routing Works

1. **Local Evaluation:** Source code is analyzed by the local compiler first.
2. **Local Clean Pass:** If 0 diagnostics are found, code is returned immediately with `status: "passed_locally"`. 0 AI calls, 100% token savings.
3. **Safe Local Fix:** If simple errors (such as missing colons or Python 2 print statements) can be deterministically fixed, `status: "resolved_locally"` is returned. 0 AI calls, 100% token savings.
4. **Focused Snippet Extraction:** If an unresolved runtime/semantic issue requires AI, SmartCompile extracts **only the relevant function or lines ±3 around the diagnostic**, not the entire source file.
5. **Cache Evaluation:** A SHA-256 key is computed over the normalized snippet, diagnostic category, error message, language, model, and provider. If found in SQLite, the response is reused instantly with `status: "cache_hit"` (0 AI calls).
6. **AI Dispatch:** On a cache miss, the focused snippet is sent to the configured AI provider. The answer is stored in SQLite cache and recorded in the audit history.

---

## 4. How Caching Works

- **Storage:** Persistent SQLite database table (`ai_cache`) in `smartcompile.db`.
- **Cache Key Formula:**
  ```python
  raw_signature = f"{language}|{provider}|{model}|{category}|{diagnostic_message}|{normalized_snippet}"
  cache_key = hashlib.sha256(raw_signature.encode("utf-8")).hexdigest()
  ```
- **Snippet Normalization:** Lines are stripped of variable line numbering prefixes, common indentation is dedented via `textwrap.dedent`, and trailing/leading blank lines are pruned.
- **Cache Invalidation:**
  - Changing the AI provider or model automatically shifts the cache key.
  - Users can clear the cache at any time from the UI with explicit confirmation (`DELETE /api/cache?confirm=true`).

---

## 5. Token Baseline & Savings Calculations

### Full-File Baseline Definition
SmartCompile compares actual usage against the standard naive AI coding assistant pattern:
- **Baseline Input:** `full_file_tokens + 250 prompt overhead tokens`
- **Baseline Output:** `max(180 tokens, full_file_tokens // 2)`
- **Baseline Total:** `baseline_input + baseline_output`

### Non-Overlapping Savings Accounting
1. **Local Resolution:** `avoided_by_local = baseline_total` (AI call avoided entirely).
2. **Cache Hit:** `avoided_by_cache = baseline_total` (AI call avoided entirely).
3. **AI Snippet Call:** `avoided_by_snippet = max(0, baseline_total - actual_tokens_used)`.
4. **Mock Simulation:** Clearly marked as simulated; never counted toward real provider billing totals.

---

## 6. Configurable AI Providers

SmartCompile supports Mock, OpenAI, Google Gemini, and Anthropic Claude.

Configure via `.env` file (copied from `.env.example`):
```env
# Active provider: mock, openai, gemini, or anthropic
AI_PROVIDER=mock

# OpenAI / OpenAI-compatible (Ollama, Groq, vLLM)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
# OPENAI_BASE_URL=https://api.openai.com/v1

# Google Gemini
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-1.5-flash

# Anthropic Claude
ANTHROPIC_API_KEY=...
ANTHROPIC_MODEL=claude-3-5-haiku-20241022
```

> **Security Note:** Secrets are strictly handled on the backend via environment variables and are **never** exposed to browser bundles or client responses.

---

## 7. Running Backend Tests

SmartCompile includes a 30-test Pytest test suite covering all 14 project criteria:

```bash
# Run pytest with verbosity
PYTHONPATH=. ./venv/bin/python -m pytest -v
```

All 30 tests pass with zero network dependency (using simulated providers and test database fixtures).
