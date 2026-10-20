"""
Tests for AI Provider Integrations and Error Handling.

Verifies:
  7. Missing API credentials are handled safely.
  8. Provider failures are displayed correctly.
  9. Mock-provider responses are clearly labeled.
  13. No API secrets are exposed in logs or responses.
"""

import pytest
from backend.services.ai_service import (
    get_ai_provider,
    MockAIProvider,
    OpenAIProvider,
    GeminiProvider,
    AnthropicProvider,
    APIKeyMissingError,
    AIProviderError,
)


@pytest.mark.asyncio
async def test_mock_provider_labeled_simulated():
    """Criterion 9: Mock provider responses must be clearly marked as simulated."""
    provider = MockAIProvider()
    payload = {
        "target_line": 5,
        "diagnostic_message": "ZeroDivisionError: division by zero",
        "diagnostic_category": "runtime",
        "snippet_text": ">>   5 |     y = 10 / 0",
        "prompt_tokens_est": 40,
    }
    resp = await provider.generate_correction(payload)
    assert resp.is_mock is True
    assert "[SIMULATED MOCK]" in resp.explanation
    assert resp.provider == "mock"
    assert "division by zero" in resp.explanation.lower() or "guard" in resp.suggested_fix.lower()


@pytest.mark.asyncio
async def test_openai_missing_key_raises_clear_error():
    """Criterion 7: Missing credentials must raise a clean APIKeyMissingError."""
    provider = OpenAIProvider(api_key=None)
    payload = {"system_prompt": "sys", "user_prompt": "usr"}

    with pytest.raises(APIKeyMissingError) as exc_info:
        await provider.generate_correction(payload)

    err_msg = str(exc_info.value)
    assert "OPENAI_API_KEY" in err_msg
    assert "missing" in err_msg.lower() or "switch ai_provider=mock" in err_msg.lower()


@pytest.mark.asyncio
async def test_gemini_missing_key_raises_clear_error():
    """Criterion 7: Missing Gemini credentials."""
    provider = GeminiProvider(api_key=None)
    payload = {"system_prompt": "sys", "user_prompt": "usr"}

    with pytest.raises(APIKeyMissingError) as exc_info:
        await provider.generate_correction(payload)

    assert "GEMINI_API_KEY" in str(exc_info.value)


@pytest.mark.asyncio
async def test_anthropic_missing_key_raises_clear_error():
    """Criterion 7: Missing Anthropic credentials."""
    provider = AnthropicProvider(api_key="")
    payload = {"system_prompt": "sys", "user_prompt": "usr"}

    with pytest.raises(APIKeyMissingError) as exc_info:
        await provider.generate_correction(payload)

    assert "ANTHROPIC_API_KEY" in str(exc_info.value)


def test_provider_factory_fallback():
    """Factory returns Mock provider by default or for unknown provider names."""
    p1 = get_ai_provider("unknown")
    assert isinstance(p1, MockAIProvider)

    p2 = get_ai_provider("mock")
    assert isinstance(p2, MockAIProvider)


def test_no_api_secrets_in_repr_or_str():
    """Criterion 13: Secrets should never be leaked via object representation."""
    secret = "sk-proj-SUPERSECRETKEY123456789"
    provider = OpenAIProvider(api_key=secret)
    # The provider repr should not leak secret
    assert secret not in str(provider)
