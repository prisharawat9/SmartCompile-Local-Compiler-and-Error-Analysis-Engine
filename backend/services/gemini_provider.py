"""
Google Gemini AI Provider for SmartCompile using the official `google-genai` SDK.

Follows the BaseAIProvider interface strictly:
  - Uses `from google import genai` with `client.aio.models.generate_content`.
  - Non-blocking execution on FastAPI event loop.
  - Sends ONLY the focused snippet + diagnostic message + line numbers + minimal context.
  - Requests structured JSON: {"explanation": str, "corrected_code": str}.
  - Uses exact usage metadata (prompt_token_count, candidates_token_count, total_token_count)
    reported by Gemini as ACTUAL tokens; falls back to ESTIMATED if missing.
  - Results are marked as real provider results (is_mock=False).
  - Handles rate limits (429) with exponential backoff up to AI_MAX_RETRIES.
  - Handles missing keys, auth/permissions (401/403), timeouts, blocked responses, and parse errors.
  - NEVER logs, prints, or exposes the API key.
"""

import asyncio
import json
import logging
import re
from typing import Dict, Any, Optional

from google import genai
from google.genai import types
from google.genai import errors

from backend.config import settings
from backend.services.ai_service import (
    BaseAIProvider,
    AIResponse,
    APIKeyMissingError,
    AIRateLimitError,
    AITimeoutError,
    AIProviderError,
)

logger = logging.getLogger("smartcompile.gemini")


class GeminiProvider(BaseAIProvider):
    """
    Google Gemini Provider implementing BaseAIProvider using the modern google-genai SDK.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        max_retries: Optional[int] = None,
    ):
        self._api_key = api_key
        self._configured_model = model
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    @property
    def name(self) -> str:
        return "gemini"

    def _get_api_key(self) -> str:
        key = self._api_key or settings.GEMINI_API_KEY
        if not key or not str(key).strip():
            raise APIKeyMissingError(
                "Gemini API key is missing. Set GEMINI_API_KEY in your .env or switch AI_PROVIDER=mock."
            )
        return str(key).strip()

    def _resolve_model(self, model_override: Optional[str] = None) -> str:
        # Check override, constructor model, or config
        model = model_override or self._configured_model or settings.get_model_for_provider("gemini")
        if not model or not str(model).strip():
            raise AIProviderError(
                "AI_MODEL configuration is missing for Gemini provider. Set AI_MODEL (e.g. gemini-2.5-flash) in your .env."
            )
        return str(model).strip()

    def _get_client(self, api_key: str) -> genai.Client:
        import httpx
        timeout = float(self.timeout_seconds or settings.AI_TIMEOUT_SECONDS or 30.0)
        # Using async_client_args with explicit httpx.Timeout prevents ConnectTimeout on Windows event loops
        return genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                async_client_args={
                    "timeout": httpx.Timeout(timeout=timeout, connect=15.0)
                }
            ),
        )

    async def generate_correction(
        self, payload: Dict[str, Any], model_override: Optional[str] = None
    ) -> AIResponse:
        api_key = self._get_api_key()
        model = self._resolve_model(model_override)
        timeout = float(self.timeout_seconds or settings.AI_TIMEOUT_SECONDS or 30.0)
        max_retries = int(self.max_retries if self.max_retries is not None else settings.AI_MAX_RETRIES)

        # Build prompt: strictly relevant snippet + diagnostic + minimal context
        system_instruction = (
            "You are SmartCompile AI, an expert compiler diagnosis and repair engine. "
            "Analyze the provided code snippet and diagnostic message. "
            "You MUST respond ONLY with valid JSON conforming to this schema:\n"
            '{"explanation": "<1-2 concise sentences explaining the root cause>", '
            '"corrected_code": "<the minimal exact corrected replacement code for the snippet>"}'
        )

        user_content = (
            f"Diagnostic: Line {payload.get('target_line', 1)}: {payload.get('diagnostic_message', 'Error')}\n"
            f"Category: {payload.get('diagnostic_category', 'syntax')}\n"
            f"Code Lines ({payload.get('line_start', 1)}-{payload.get('line_end', 1)}):\n"
            f"```\n{payload.get('snippet_text', '')}\n```\n"
            "Return JSON with 'explanation' and 'corrected_code'."
        )

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            temperature=0.2,
        )

        client = self._get_client(api_key)

        attempts = 0
        backoff_seconds = 1.0

        while True:
            attempts += 1
            try:
                # Execute non-blocking async call with timeout guard
                response = await asyncio.wait_for(
                    client.aio.models.generate_content(
                        model=model,
                        contents=user_content,
                        config=config,
                    ),
                    timeout=timeout,
                )
                break
            except asyncio.TimeoutError:
                raise AITimeoutError(
                    f"Gemini request timed out after {timeout}s while contacting model '{model}'."
                )
            except errors.APIError as e:
                status_code = getattr(e, "code", None)
                raw_err = str(e)
                # Sanitize to never leak API keys if present in raw error text
                err_text = raw_err.replace(api_key, "[REDACTED]") if api_key else raw_err

                # Check for 429 rate limit or quota exhaustion
                if status_code == 429 or "429" in err_text or "RESOURCE_EXHAUSTED" in err_text:
                    if attempts <= max_retries:
                        logger.warning(
                            f"Gemini rate limit encountered (attempt {attempts}/{max_retries + 1}). "
                            f"Retrying in {backoff_seconds}s..."
                        )
                        await asyncio.sleep(backoff_seconds)
                        backoff_seconds *= 2.0
                        continue
                    raise AIRateLimitError(
                        f"Gemini rate limit or quota exceeded for model '{model}' after {attempts} attempts. "
                        "Please check your API quota or retry later."
                    )
                # Check for 400 / 401 / 403 API key or permission issues
                if (
                    status_code in (401, 403)
                    or "API_KEY_INVALID" in err_text
                    or "PERMISSION_DENIED" in err_text
                    or "API key not valid" in err_text
                ):
                    raise APIKeyMissingError(
                        "Gemini authentication failed: Invalid API key or permission denied."
                    )
                # Check for bad request / model not found
                if status_code == 404 or "NOT_FOUND" in err_text:
                    raise AIProviderError(
                        f"Gemini model '{model}' was not found or is unavailable for your API key."
                    )
                # Check for 503 high demand / service unavailable
                if status_code == 503 or "503" in err_text or "UNAVAILABLE" in err_text:
                    if attempts <= max_retries:
                        await asyncio.sleep(backoff_seconds)
                        backoff_seconds *= 2.0
                        continue
                    raise AIProviderError(
                        f"Gemini model '{model}' is currently experiencing high demand (503 UNAVAILABLE). Please try again shortly."
                    )
                # Generic provider error
                raise AIProviderError(f"Gemini API error ({status_code or 'unknown'}): {err_text or type(e).__name__}")
            except Exception as e:
                raw_err = str(e) or repr(e)
                err_str = raw_err.replace(api_key, "[REDACTED]") if api_key else raw_err

                if "429" in err_str or "quota" in err_str.lower() or "RESOURCE_EXHAUSTED" in err_str:
                    if attempts <= max_retries:
                        await asyncio.sleep(backoff_seconds)
                        backoff_seconds *= 2.0
                        continue
                    raise AIRateLimitError(f"Gemini rate limit or quota exceeded: {err_str}")
                if "API_KEY" in err_str.upper() or "PERMISSION" in err_str.upper():
                    raise APIKeyMissingError("Gemini authentication failed: Invalid API key or permission denied.")
                if "ConnectTimeout" in err_str or "timeout" in err_str.lower() or isinstance(e, asyncio.TimeoutError):
                    raise AITimeoutError(f"Gemini connection timed out after {timeout}s while contacting '{model}'.")
                raise AIProviderError(f"Network or provider error contacting Gemini: {type(e).__name__}: {err_str}")

        # Extract content text safely
        raw_text = ""
        if response and response.text:
            raw_text = response.text.strip()
        elif response and response.candidates:
            parts = response.candidates[0].content.parts if response.candidates[0].content else []
            raw_text = "".join([getattr(p, "text", "") or "" for p in parts]).strip()

        if not raw_text:
            raise AIProviderError("Gemini returned an empty or blocked response.")

        # Parse JSON output safely
        try:
            # Handle potential markdown fence wrapping like ```json ... ```
            cleaned_text = raw_text
            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw_text)
            if match:
                cleaned_text = match.group(1).strip()
            parsed = json.loads(cleaned_text)
            if not isinstance(parsed, dict):
                raise ValueError("Response JSON is not an object")
            explanation = str(parsed.get("explanation") or "").strip()
            corrected_code = str(parsed.get("corrected_code") or parsed.get("suggested_fix") or "").strip()
            if not explanation and not corrected_code:
                raise ValueError("JSON response missing 'explanation' and 'corrected_code' fields")
        except Exception as e:
            raise AIProviderError(
                f"Gemini returned invalid structured JSON response: {str(e)}"
            )

        # Extract tokens from usage metadata
        input_tokens = 0
        output_tokens = 0
        usage = getattr(response, "usage_metadata", None)
        if usage:
            input_tokens = int(getattr(usage, "prompt_token_count", 0) or 0)
            output_tokens = int(getattr(usage, "candidates_token_count", 0) or 0)

        # If usage metadata is missing or zero, fallback token estimation occurs in token_accounting
        return AIResponse(
            explanation=explanation,
            suggested_fix=corrected_code,
            corrected_snippet=corrected_code,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            provider="gemini",
            model=model,
            is_mock=False,
            raw_response=raw_text,
        )
