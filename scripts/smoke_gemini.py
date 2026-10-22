"""
Manual Smoke Test Script for Google Gemini Provider.

Executes ONE real Gemini API call with a minimal focused snippet
and prints the structured explanation, suggested fix, and token usage.
NEVER prints, logs, or displays the API key.
"""

import asyncio
import os
import sys

# Ensure root directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.config import settings
from backend.services.gemini_provider import GeminiProvider


async def run_smoke_test():
    print("=" * 60)
    print(" SmartCompile — Google Gemini Provider Smoke Test")
    print("=" * 60)

    # Check API key configuration without displaying it
    has_key = bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip())
    model = settings.get_model_for_provider("gemini")

    print(f"Provider:             gemini")
    print(f"Target Model:         {model or '(not set)'}")
    print(f"API Key Configured:   {has_key} (secret masked)")
    print(f"Timeout (seconds):    {settings.AI_TIMEOUT_SECONDS}")
    print("-" * 60)

    if not has_key:
        print("[ERROR] GEMINI_API_KEY is not configured in your environment or .env file.")
        print("Please set GEMINI_API_KEY and AI_MODEL (e.g. gemini-2.5-flash) in your .env file.")
        sys.exit(1)

    if not model:
        print("[ERROR] AI_MODEL is not configured for Gemini.")
        print("Please set AI_MODEL=gemini-2.5-flash (or gemini-1.5-flash) in your .env file.")
        sys.exit(1)

    provider = GeminiProvider()

    sample_payload = {
        "target_line": 2,
        "line_start": 1,
        "line_end": 3,
        "diagnostic_message": "ZeroDivisionError: division by zero",
        "diagnostic_category": "runtime",
        "snippet_text": ">>   2 |     avg = total / count",
    }

    print("Sending focused diagnostic snippet to Gemini...")
    try:
        response = await provider.generate_correction(sample_payload)
        print("\n[SUCCESS] Response received from Google Gemini API:")
        print(f"  • Explanation:       {response.explanation}")
        print(f"  • Corrected Code:    {response.suggested_fix}")
        print(f"  • Model Used:        {response.model}")
        print(f"  • Input Tokens:      {response.input_tokens}")
        print(f"  • Output Tokens:     {response.output_tokens}")
        print(f"  • Total Tokens:      {response.input_tokens + response.output_tokens}")
        print(f"  • Is Simulated Mock: {response.is_mock}")
        print("=" * 60)
    except Exception as e:
        print(f"\n[FAILURE] Error contacting Gemini: {type(e).__name__}: {str(e)}")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_smoke_test())
