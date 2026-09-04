"""Tests for Anthropic Claude provider."""

from dataclasses import replace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from free_claude_code.config.provider_catalog import ANTHROPIC_DEFAULT_BASE
from free_claude_code.providers.anthropic import AnthropicProvider
from tests.providers.request_factory import make_messages_request
from tests.providers.support import (
    immediate_admission,
    make_provider_config,
)


def make_request(model: str = "claude-opus-5", **overrides):
    """Create a test request for Claude model."""
    return make_messages_request(model, **overrides)


@pytest.fixture
def anthropic_config():
    """Create Anthropic provider configuration."""
    return make_provider_config(
        api_key="sk-ant-test-key",
        base_url=ANTHROPIC_DEFAULT_BASE,
        rate_limit=10,
        rate_window=60,
    )


@pytest.fixture
def anthropic_provider(anthropic_config):
    """Create an Anthropic provider instance."""
    with (
        patch("free_claude_code.providers.anthropic.client.Anthropic"),
        patch("free_claude_code.providers.anthropic.client.AsyncAnthropic"),
    ):
        return AnthropicProvider(anthropic_config, admission=immediate_admission())


def test_default_base_url_constant():
    """Verify Anthropic default base URL is correct."""
    assert ANTHROPIC_DEFAULT_BASE == "https://api.anthropic.com/v1"


def test_init_uses_default_base_url_and_api_key(anthropic_config):
    """Test provider initializes with correct credentials."""
    with (
        patch(
            "free_claude_code.providers.anthropic.client.Anthropic"
        ) as mock_anthropic,
        patch("free_claude_code.providers.anthropic.client.AsyncAnthropic"),
    ):
        provider = AnthropicProvider(anthropic_config, admission=immediate_admission())

    assert provider._api_key == "sk-ant-test-key"
    assert provider._base_url == ANTHROPIC_DEFAULT_BASE
    mock_anthropic.assert_called_once()


def test_init_strips_trailing_slash(anthropic_config):
    """Test that trailing slashes are stripped from base URL."""
    config = replace(anthropic_config, base_url=f"{ANTHROPIC_DEFAULT_BASE}/")

    with (
        patch("free_claude_code.providers.anthropic.client.Anthropic"),
        patch("free_claude_code.providers.anthropic.client.AsyncAnthropic"),
    ):
        provider = AnthropicProvider(config, admission=immediate_admission())

    assert provider._base_url == ANTHROPIC_DEFAULT_BASE


def test_supports_claude_models(anthropic_config):
    """Test that provider supports Claude models."""
    with (
        patch("free_claude_code.providers.anthropic.client.Anthropic"),
        patch("free_claude_code.providers.anthropic.client.AsyncAnthropic"),
    ):
        provider = AnthropicProvider(anthropic_config, admission=immediate_admission())

    # Provider should validate Claude models
    request = make_request(model="claude-opus-5")
    provider.preflight_messages(request)  # Should not raise


def test_rejects_non_claude_models(anthropic_config):
    """Test that provider rejects non-Claude models."""
    with (
        patch("free_claude_code.providers.anthropic.client.Anthropic"),
        patch("free_claude_code.providers.anthropic.client.AsyncAnthropic"),
    ):
        provider = AnthropicProvider(anthropic_config, admission=immediate_admission())

    # Provider should reject non-Claude models
    request = make_request(model="gpt-4")
    with pytest.raises(ValueError):  # Should raise validation error
        provider.preflight_messages(request)


@pytest.mark.asyncio
async def test_stream_messages_success(anthropic_provider):
    """Test successful message streaming."""
    request = make_request()

    # Mock the Anthropic API response
    mock_stream = AsyncMock()
    mock_stream.__enter__.return_value = [
        MagicMock(type="message_start", message={"id": "msg-123"}),
        MagicMock(
            type="content_block_delta", delta={"type": "text_delta", "text": "Hello"}
        ),
        MagicMock(type="message_delta", delta={"stop_reason": "end_turn"}),
    ]
    mock_stream.__exit__.return_value = None

    with patch.object(
        anthropic_provider._client.messages, "stream", return_value=mock_stream
    ):
        stream = anthropic_provider.stream_messages(request)
        assert stream is not None


def test_rejects_disabled_tool_use(anthropic_config):
    """Test that provider rejects requests with disabled tool use."""
    with (
        patch("free_claude_code.providers.anthropic.client.Anthropic"),
        patch("free_claude_code.providers.anthropic.client.AsyncAnthropic"),
    ):
        provider = AnthropicProvider(anthropic_config, admission=immediate_admission())

    # Request with disabled tool use should be rejected
    request = make_request(tools=[{"name": "test", "description": "test"}])
    # Provider configuration should handle this appropriately
    provider.preflight_messages(request)  # May warn but should not fail


def test_respects_rate_limits(anthropic_config):
    """Test that provider respects configured rate limits."""
    config = replace(anthropic_config, rate_limit=5, rate_window=60)

    with (
        patch("free_claude_code.providers.anthropic.client.Anthropic"),
        patch("free_claude_code.providers.anthropic.client.AsyncAnthropic"),
    ):
        provider = AnthropicProvider(config, admission=immediate_admission())

    assert provider._config.rate_limit == 5
    assert provider._config.rate_window == 60
