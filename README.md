# SmartCompile — AI-Assisted Compiler with Token Optimization

## 1. Project Overview

SmartCompile is an AI-assisted compiler designed to make code error detection and resolution more efficient while reducing unnecessary AI API token consumption.

Traditional AI coding assistants may send large portions of source code to an AI model for debugging. SmartCompile follows a smarter approach by performing lexical, syntax, and semantic analysis locally before deciding whether AI assistance is necessary.

Common programming errors are identified and handled locally wherever possible. Only unresolved errors that benefit from AI assistance are forwarded to an AI model, using relevant code snippets instead of the entire source file. A caching mechanism stores previous AI responses to avoid repeated API requests for equivalent errors.

The application also provides an interactive dashboard that displays compiler diagnostics, AI usage, cache statistics, and estimated token savings.

## 2. Problem Statement

AI-assisted coding tools can consume significant API tokens when repeatedly analyzing entire source files, even when errors could be detected using traditional compiler techniques.

This can increase API costs, introduce unnecessary network requests, and make error resolution less efficient.

SmartCompile addresses this problem by combining conventional compiler analysis with selective AI integration, focused code-context transmission, and response caching.

## 3. Project Objectives

- Detect common programming errors using local compiler analysis.
- Implement lexical, syntax, and semantic error checking.
- Resolve straightforward errors locally where safe and practical.
- Route only suitable unresolved errors to an AI model.
- Minimize the amount of source code sent to the AI provider.
- Cache previous AI responses to reduce repeated API calls.
- Track AI requests, token usage, cache hits, and estimated token savings.
- Provide an interactive dashboard for monitoring compiler and AI activity.
- Demonstrate the integration of traditional compiler design and modern AI-assisted development.

## 4. Key Features

### Local Compiler Analysis
Analyzes source code locally to identify supported lexical, syntax, and semantic errors without requiring an AI API call.

### Intelligent AI Routing
Forwards unresolved errors to an AI model only when additional assistance is appropriate.

### Partial Code Transmission
Sends relevant code snippets and diagnostic context rather than transmitting the entire source file by default.

### Response Caching
Stores AI responses for equivalent requests and reuses valid cached results to avoid unnecessary API calls.

### Automatic Fix Suggestions
Provides deterministic local fixes for supported errors when corrections are safe and unambiguous. AI-assisted corrections can also be proposed for more complex issues.

### Token Usage Analytics
Tracks provider-reported token usage where available and estimates usage when actual measurements are unavailable.

### Interactive Dashboard
Displays compiler diagnostics, error categories, AI requests, cache statistics, compilation history, and estimated token savings.

## 5. System Architecture

SmartCompile follows a modular architecture consisting of the following components:

1. **Code Editor:** Accepts source code from the user.
2. **Local Compiler Engine:** Performs lexical, syntax, and semantic analysis.
3. **Error Classification:** Separates locally diagnosable errors from unresolved issues.
4. **AI Routing Module:** Determines whether an unresolved issue should be sent to an AI model.
5. **Cache Manager:** Checks for reusable responses before making an AI request.
6. **AI Service:** Analyzes relevant code snippets when additional assistance is required.
7. **Token Tracking Module:** Records API usage, cache activity, and estimated savings.
8. **Dashboard:** Presents diagnostics, proposed fixes, and optimization statistics.

### Workflow

User Code → Local Compiler Analysis → Error Classification → Cache Lookup → AI Assistance if Required → Results and Diagnostics → Usage Dashboard

If an error can be handled locally, the application avoids an AI request. If an equivalent valid cached response exists, it can be reused without another request to the AI provider.

## 6. Technology Stack

| Component | Technology |
|---|---|
| Backend | Python |
| Backend API | FastAPI |
| Lexical Analysis | Python `tokenize` |
| Syntax Analysis | Python `ast` |
| Semantic Analysis | Custom AST-based analysis |
| Frontend | React and TypeScript |
| Code Editor | Monaco Editor |
| Database and Cache | SQLite |
| AI Integration | Configurable AI provider API |
| Dashboard Charts | Recharts |
| Testing | Pytest |
| Version Control | Git and GitHub |

*The technology stack represents the planned implementation. Update this section if the final implementation uses different tools.*

## 7. Project Structure

The project is organized into separate frontend, compiler, AI, and analytics modules.

```text
SmartCompile/
├── backend/
│   ├── compiler/
│   │   └── analyzer.py
│   ├── ai/
│   │   ├── router.py
│   │   └── provider.py
│   ├── cache/
│   │   └── manager.py
│   ├── analytics/
│   │   └── token_tracker.py
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── package.json
│   └── index.html
├── tests/
├── .env.example
├── .gitignore
└── README.md
```

The exact directory structure may evolve during development.

## 8. Installation and Setup

### Prerequisites

Install the following before running the project:

- Python 3.11 or newer
- Node.js 20 or newer
- npm
- Git
- An API key for the selected AI provider, if using real AI integration

### Step 1: Clone the Repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd SmartCompile
```

Replace the placeholder with your actual repository URL.

### Step 2: Set Up the Backend

Create and activate a Python virtual environment.

**macOS/Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows PowerShell:**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Install the backend dependencies:

```bash
pip install -r backend/requirements.txt
```

If the dependency file has not been created yet, install the packages listed in the actual implementation before continuing.

### Step 3: Configure Environment Variables

Create a local `.env` file using `.env.example` as a reference.

Example:

```env
AI_API_KEY=your_api_key_here
AI_MODEL=your_selected_model
```

Use the variable names required by your actual AI provider integration. Never commit the `.env` file or expose API credentials in frontend code.

### Step 4: Start the Backend

From the project root, run:

```bash
uvicorn backend.main:app --reload
```

If the backend entry point or package structure differs, use the command documented by the implementation.

When running locally, the FastAPI interactive documentation is generally available at:

`http://127.0.0.1:8000/docs`

### Step 5: Start the Frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the local URL printed by the frontend development server.

The frontend must be configured to communicate with the running backend API.

## 9. How to Use SmartCompile

1. Open the application in your browser.
2. Enter or paste Python source code into the editor.
3. Select **Analyze** or **Compile**.
4. Review the locally generated compiler diagnostics.
5. Inspect any available local fix suggestions.
6. Allow unresolved issues to be routed to AI when appropriate.
7. Review the AI explanation and proposed correction, if returned.
8. Repeat an equivalent AI-assisted request to demonstrate caching.
9. Open the dashboard to inspect AI calls, token usage, cache hits, and estimated savings.

Actual AI-assisted functionality requires a correctly configured provider. If a mock-provider mode is available, simulated results must be clearly distinguished from real provider responses.

## 10. API Overview

The following endpoints describe the planned backend interface. Confirm the final paths against the implemented application.

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/analyze` | Run local compiler analysis |
| POST | `/api/compile` | Run the complete analysis and AI-routing workflow |
| GET | `/api/stats` | Retrieve usage and optimization statistics |
| GET | `/api/history` | Retrieve recent compilation history |
| GET | `/api/cache/stats` | Retrieve cache statistics |
| DELETE | `/api/cache` | Clear cached AI responses |
| GET | `/api/health` | Check backend health |

## 11. Token Optimization Strategy

SmartCompile uses three main optimization techniques.

**1. Local Error Handling**

Errors that can be diagnosed and handled locally do not require an AI API request.

**2. Partial Code Transmission**

Only the relevant source snippet and necessary diagnostic context are sent to the AI model by default, reducing unnecessary input tokens.

**3. Response Caching**

Equivalent requests can reuse previously stored AI responses, avoiding repeated requests when the cache entry remains valid.

Token savings are calculated against a defined baseline. Actual provider-reported token usage should be distinguished from estimates, and overlapping savings must not be counted twice.

## 12. Testing and Evaluation

The project should be tested using the following scenarios:

- Valid source code with no errors.
- Common syntax errors handled locally.
- Supported semantic errors.
- Safe local fix suggestions.
- Unresolved errors that require AI assistance.
- Repeated equivalent requests that produce cache hits.
- Missing or invalid AI API credentials.
- AI provider failures and timeouts.
- Token usage and savings calculations.
- Dashboard metrics and compilation history.

Automated backend tests can be run using:

```bash
pytest
```

The final evaluation should compare the number of AI requests and token usage against a clearly defined baseline, while verifying that cached responses do not trigger additional AI requests.

## 13. Team Contributions

### Person 1 — Compiler and Error Analysis
- Lexical analysis.
- Syntax analysis.
- Semantic analysis.
- Local error detection and safe fixes.
- Structured diagnostics.
- Compiler tests and integration interface.

### Person 2 — AI Optimization and Dashboard
- AI routing and provider integration.
- Partial code-context transmission.
- Response caching.
- Token usage tracking and savings calculations.
- Dashboard and charts.
- End-to-end integration and testing.

Both team members collaborate on integration, testing, documentation, and final project validation.

## 14. Expected Outcome

SmartCompile aims to demonstrate that traditional compiler techniques can be combined with selective AI assistance to create a more efficient debugging workflow.

By handling supported errors locally, transmitting focused code snippets, and reusing cached responses, the system is designed to reduce unnecessary AI API requests and token consumption while providing useful diagnostics and correction suggestions through an interactive dashboard.

Actual savings and error-resolution performance will depend on the implementation, selected AI model, request context, and workload.

## 15. Future Enhancements

- Support for additional programming languages.
- More advanced semantic analysis.
- Improved safe automatic correction.
- Better error-context extraction.
- Configurable AI providers and models.
- More detailed performance and cost comparisons.
- User accounts and project history.
- Benchmarking against a full-file AI debugging baseline.

## 16. License

Add the license selected for this project before distributing it publicly.

---

**SmartCompile — Smarter Error Detection. Selective AI. Reduced Token Usage.**
