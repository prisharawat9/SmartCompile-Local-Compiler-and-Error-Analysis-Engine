"""
AI Provider Service for SmartCompile.

Features:
  - Clean BaseAIProvider interface for modularity.
  - Providers: Mock (for offline demos and testing), OpenAI, Google Gemini, Anthropic.
  - Robust error handling: missing keys, rate limits, timeouts, bad responses.
  - Clear distinction between real provider tokens and simulated mock tokens.
  - Absolute secrecy: no API keys are ever leaked into logs or responses.
"""

from abc import ABC, abstractmethod
import json
import logging
import re
from typing import Dict, Any, Optional
import httpx
from pydantic import BaseModel, Field
from backend.config import settings

logger = logging.getLogger("smartcompile.ai")


class AIResponse(BaseModel):
    explanation: str = Field(..., description="Root cause explanation")
    suggested_fix: str = Field(..., description="Targeted fix for the error line")
    corrected_snippet: Optional[str] = Field(default=None, description="Corrected snippet")
    input_tokens: int = Field(default=0, description="Tokens in prompt (actual or simulated)")
    output_tokens: int = Field(default=0, description="Tokens in completion (actual or simulated)")
    provider: str = Field(..., description="Name of the AI provider")
    model: str = Field(..., description="Name of model used")
    is_mock: bool = Field(default=False, description="True if simulated by MockProvider")
    raw_response: Optional[str] = Field(default=None)


class AIProviderError(Exception):
    """Base exception for AI provider failures."""
    pass


class APIKeyMissingError(AIProviderError):
    """Raised when an active provider is requested without an API key."""
    pass


class AIRateLimitError(AIProviderError):
    """Raised on HTTP 429 rate limit errors."""
    pass


class AITimeoutError(AIProviderError):
    """Raised when the AI provider times out."""
    pass


class BaseAIProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    async def generate_correction(
        self, payload: Dict[str, Any], model_override: Optional[str] = None
    ) -> AIResponse:
        pass


class MockAIProvider(BaseAIProvider):
    """
    Mock AI Provider for development, offline testing, and college presentations.
    Produces realistic contextual suggestions without consuming API tokens or requiring keys.
    Results are clearly flagged as is_mock=True.
    """
    @property
    def name(self) -> str:
        return "mock"

    async def generate_correction(
        self, payload: Dict[str, Any], model_override: Optional[str] = None
    ) -> AIResponse:
        target_line = payload.get("target_line", 1)
        diag_msg = payload.get("diagnostic_message", "")
        diag_cat = payload.get("diagnostic_category", "syntax")
        snippet = payload.get("snippet_text", "")
        model = model_override or "mock-smartcompile-v1"

        # Heuristic explanation generator
        explanation = f"Detected {diag_cat} issue around line {target_line}: {diag_msg}."
        suggested_fix = "# Suggested fix: ensure variable is defined and syntax is valid"

        if "NameError" in diag_msg or "not defined" in diag_msg:
            var_match = re.search(r"name '(\w+)' is not defined", diag_msg)
            var_name = var_match.group(1) if var_match else "variable"
            explanation = f"Variable '{var_name}' is referenced on line {target_line} before assignment or import."
            suggested_fix = f"{var_name} = 0  # Initialized {var_name} before use"

        elif "ZeroDivisionError" in diag_msg or "division by zero" in diag_msg:
            explanation = f"Potential division by zero on line {target_line}. Add a guard condition to prevent ZeroDivisionError."
            suggested_fix = "if divisor != 0:\n    result = value / divisor\nelse:\n    result = 0"

        elif "TypeError" in diag_msg or "unsupported operand" in diag_msg:
            explanation = f"Type mismatch on line {target_line}. Operands have incompatible types."
            suggested_fix = "# Ensure explicit type conversion, e.g. int(val) or str(val)"

        elif "IndexError" in diag_msg or "out of range" in diag_msg:
            explanation = f"Index out of range on line {target_line}. Array/list boundary exceeded."
            suggested_fix = "if 0 <= index < len(items):\n    val = items[index]"

        elif "SyntaxError" in diag_msg:
            explanation = f"Syntax error at line {target_line}. The statement violates Python grammar."
            suggested_fix = "# Review syntax structure, parentheses, and indentation"

        # Clean snippet lines for corrected snippet
        clean_lines = []
        for line in snippet.splitlines():
            # Remove line numbering prefix e.g. '>>  12 | '
            cleaned = re.sub(r"^(>>|\s{2})\s*\d+\s*\|\s*", "", line)
            clean_lines.append(cleaned)
        corrected_snippet = "\n".join(clean_lines)

        # Simulated token calculation
        prompt_tokens_sim = payload.get("prompt_tokens_est", 60)
        output_tokens_sim = 45

        return AIResponse(
            explanation=f"[SIMULATED MOCK] {explanation}",
            suggested_fix=suggested_fix,
            corrected_snippet=corrected_snippet,
            input_tokens=prompt_tokens_sim,
            output_tokens=output_tokens_sim,
            provider="mock",
            model=model,
            is_mock=True,
            raw_response=json.dumps({"explanation": explanation, "suggested_fix": suggested_fix}),
        )


class OpenAIProvider(BaseAIProvider):
    """
    OpenAI and OpenAI-compatible API provider (e.g. Ollama, Groq, OpenRouter).
    """
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.base_url = (base_url or settings.OPENAI_BASE_URL or "https://api.openai.com/v1").rstrip("/")

    @property
    def name(self) -> str:
        return "openai"

    async def generate_correction(
        self, payload: Dict[str, Any], model_override: Optional[str] = None
    ) -> AIResponse:
        if not self.api_key or not self.api_key.strip():
            raise APIKeyMissingError(
                "OpenAI API key is missing. Set OPENAI_API_KEY in your .env or switch AI_PROVIDER=mock."
            )

        model = model_override or settings.OPENAI_MODEL
        headers = {
            "Authorization": f"Bearer {self.api_key.strip()}",
            "Content-Type": "application/json",
        }

        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": payload["system_prompt"]},
                {"role": "user", "content": payload["user_prompt"]},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }

        url = f"{self.base_url}/chat/completions"
        try:
            async with httpx.AsyncClient(timeout=settings.AI_REQUEST_TIMEOUT) as client:
                res = await client.post(url, headers=headers, json=body)
        except httpx.TimeoutException:
            raise AITimeoutError(f"OpenAI request timed out after {settings.AI_REQUEST_TIMEOUT}s.")
        except Exception as e:
            raise AIProviderError(f"Network error contacting OpenAI: {str(e)}")

        if res.status_code == 401:
            raise APIKeyMissingError("OpenAI authentication failed. Invalid API key provided.")
        elif res.status_code == 429:
            raise AIRateLimitError("OpenAI rate limit or quota exceeded. Check billing/credits.")
        elif res.status_code >= 400:
            raise AIProviderError(f"OpenAI API error {res.status_code}: {res.text}")

        data = res.json()
        usage = data.get("usage", {})
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)

        content = data["choices"][0]["message"]["content"]
        try:
            parsed = json.loads(content)
            explanation = parsed.get("explanation", "AI analyzed the snippet.")
            suggested_fix = parsed.get("suggested_fix", "")
            corrected_snippet = parsed.get("corrected_snippet", None)
        except Exception:
            explanation = content
            suggested_fix = ""
            corrected_snippet = None

        return AIResponse(
            explanation=explanation,
            suggested_fix=suggested_fix,
            corrected_snippet=corrected_snippet,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            provider="openai",
            model=model,
            is_mock=False,
            raw_response=content,
        )


from backend.services.gemini_provider import GeminiProvider


class AnthropicProvider(BaseAIProvider):
    """Anthropic Claude AI Provider."""
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY

    @property
    def name(self) -> str:
        return "anthropic"

    async def generate_correction(
        self, payload: Dict[str, Any], model_override: Optional[str] = None
    ) -> AIResponse:
        if not self.api_key or not self.api_key.strip():
            raise APIKeyMissingError(
                "Anthropic API key is missing. Set ANTHROPIC_API_KEY in your .env or switch AI_PROVIDER=mock."
            )

        model = model_override or settings.ANTHROPIC_MODEL
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key.strip(),
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        body = {
            "model": model,
            "max_tokens": 1000,
            "system": payload["system_prompt"],
            "messages": [{"role": "user", "content": payload["user_prompt"]}],
            "temperature": 0.2,
        }

        try:
            async with httpx.AsyncClient(timeout=settings.AI_REQUEST_TIMEOUT) as client:
                res = await client.post(url, headers=headers, json=body)
        except httpx.TimeoutException:
            raise AITimeoutError(f"Anthropic request timed out after {settings.AI_REQUEST_TIMEOUT}s.")
        except Exception as e:
            raise AIProviderError(f"Network error contacting Anthropic: {str(e)}")

        if res.status_code == 401:
            raise APIKeyMissingError("Invalid or unauthorized Anthropic API key (ANTHROPIC_API_KEY).")
        elif res.status_code == 429:
            raise AIRateLimitError("Anthropic rate limit exceeded.")
        elif res.status_code >= 400:
            raise AIProviderError(f"Anthropic API error {res.status_code}: {res.text}")

        data = res.json()
        usage = data.get("usage", {})
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)

        content_list = data.get("content", [])
        text = content_list[0].get("text", "") if content_list else ""
        try:
            # Extract JSON block if wrapped in markdown
            json_text = text
            match = re.search(r"```json\s*([\s\S]*?)\s*```", text)
            if match:
                json_text = match.group(1)
            parsed = json.loads(json_text)
            explanation = parsed.get("explanation", "AI analyzed snippet.")
            suggested_fix = parsed.get("suggested_fix", "")
            corrected_snippet = parsed.get("corrected_snippet", None)
        except Exception:
            explanation = text
            suggested_fix = ""
            corrected_snippet = None

        return AIResponse(
            explanation=explanation,
            suggested_fix=suggested_fix,
            corrected_snippet=corrected_snippet,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            provider="anthropic",
            model=model,
            is_mock=False,
            raw_response=text,
        )


def get_ai_provider(provider_name: Optional[str] = None) -> BaseAIProvider:
    """Factory function returning the configured AI provider instance."""
    prov = (provider_name or settings.active_provider).lower().strip()
    if prov == "openai":
        return OpenAIProvider()
    elif prov == "gemini":
        return GeminiProvider()
    elif prov == "anthropic":
        return AnthropicProvider()
    else:
        return MockAIProvider()
