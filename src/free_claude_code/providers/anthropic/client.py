"""Anthropic Claude provider implementation."""

import json
from collections.abc import AsyncIterator
from typing import Any

from anthropic import Anthropic, AsyncAnthropic
from loguru import logger

from free_claude_code.application.model_metadata import ProviderModelInfo
from free_claude_code.core.anthropic.models import MessagesRequest
from free_claude_code.core.openai_responses import OpenAIResponsesRequest
from free_claude_code.core.reasoning import DEFAULT_REASONING_POLICY, ReasoningPolicy
from free_claude_code.providers.admission import ProviderAdmissionController
from free_claude_code.providers.base import BaseProvider, ProviderConfig

# Known Claude models available from Anthropic
_CLAUDE_MODELS = {
    "claude-opus-5": {"supports_thinking": True},
    "claude-sonnet-5": {"supports_thinking": True},
    "claude-haiku-4-5-20251001": {"supports_thinking": True},
}


class AnthropicProvider(BaseProvider):
    """Anthropic Claude API provider using official SDK."""

    def __init__(
        self,
        config: ProviderConfig,
        *,
        admission: ProviderAdmissionController,
    ) -> None:
        super().__init__(config)
        self._api_key = config.api_key
        self._base_url = config.base_url.rstrip("/")
        self._admission = admission

        # Initialize both sync and async clients
        self._client = Anthropic(
            api_key=self._api_key,
            base_url=self._base_url,
        )
        self._async_client = AsyncAnthropic(
            api_key=self._api_key,
            base_url=self._base_url,
        )

    def preflight_messages(
        self,
        request: MessagesRequest,
        *,
        reasoning: ReasoningPolicy = DEFAULT_REASONING_POLICY,
    ) -> None:
        """Validate that request uses Claude models."""
        model = request.model
        if not model.startswith("claude-"):
            raise ValueError(
                f"Anthropic provider only supports Claude models, got {model!r}"
            )

    def preflight_responses(
        self,
        request: OpenAIResponsesRequest,
        *,
        reasoning: ReasoningPolicy = DEFAULT_REASONING_POLICY,
    ) -> None:
        """Anthropic provider does not support Responses format."""
        raise NotImplementedError(
            "Anthropic provider does not support OpenAI Responses format"
        )

    async def cleanup(self) -> None:
        """Release async client resources."""
        await self._async_client.close()

    async def list_model_infos(self) -> frozenset[ProviderModelInfo]:
        """Return available Claude models."""
        models = set()
        for model_id, info in _CLAUDE_MODELS.items():
            models.add(
                ProviderModelInfo(
                    model_id=model_id,
                    supports_thinking=info.get("supports_thinking"),
                )
            )
        return frozenset(models)

    def stream_messages(
        self,
        request: MessagesRequest,
        input_tokens: int = 0,
        *,
        request_id: str | None = None,
        response_model: str | None = None,
        reasoning: ReasoningPolicy = DEFAULT_REASONING_POLICY,
    ) -> AsyncIterator[str]:
        """Stream response from Anthropic API in Anthropic SSE format."""
        # Validate request
        self.preflight_messages(request, reasoning=reasoning)

        # Build request kwargs for Anthropic API
        kwargs: dict[str, Any] = {
            "model": request.model,
            "max_tokens": request.max_tokens or 4096,
            "messages": _convert_messages(request.messages),
            "stream": True,
        }

        # Add optional fields
        if request.system:
            kwargs["system"] = request.system
        if request.temperature is not None:
            kwargs["temperature"] = request.temperature
        if request.top_p is not None:
            kwargs["top_p"] = request.top_p
        if request.top_k is not None:
            kwargs["top_k"] = request.top_k
        if request.stop_sequences:
            kwargs["stop_sequences"] = request.stop_sequences
        if request.tools:
            kwargs["tools"] = _convert_tools(request.tools)
        if request.tool_choice:
            kwargs["tool_choice"] = request.tool_choice
        if request.thinking:
            kwargs["thinking"] = _convert_thinking_config(request.thinking)

        # Stream from API
        try:
            with self._client.messages.stream(**kwargs) as stream:
                for event in stream:
                    # Convert SDK events to Anthropic SSE format
                    sse_text = _format_sse_event(event)
                    if sse_text:
                        yield sse_text
        except Exception as e:
            logger.error(
                "ANTHROPIC_STREAM: streaming error exc_type={} request_id={}",
                type(e).__name__,
                request_id,
            )
            self._log_stream_transport_error(
                "ANTHROPIC",
                "STREAM",
                e,
                request_id=request_id,
            )
            raise

    def stream_responses(
        self,
        request: OpenAIResponsesRequest,
        input_tokens: int = 0,
        *,
        request_id: str | None = None,
        response_model: str | None = None,
        reasoning: ReasoningPolicy = DEFAULT_REASONING_POLICY,
    ) -> AsyncIterator[str]:
        """Anthropic provider does not support Responses format."""
        raise NotImplementedError(
            "Anthropic provider does not support OpenAI Responses format"
        )
        # Make this a generator function (unreachable but needed for type)
        yield  # pragma: no cover


def _convert_messages(messages: list[Any]) -> list[dict[str, Any]]:
    """Convert internal Message format to Anthropic SDK format."""
    result = []
    for msg in messages:
        if isinstance(msg, dict):
            result.append(msg)
        else:
            # Handle Message dataclass or similar
            result.append(msg.model_dump() if hasattr(msg, "model_dump") else msg)
    return result


def _convert_tools(tools: list[Any]) -> list[dict[str, Any]]:
    """Convert internal Tool format to Anthropic SDK format."""
    result = []
    for tool in tools:
        if isinstance(tool, dict):
            result.append(tool)
        else:
            # Handle Tool dataclass or similar
            result.append(tool.model_dump() if hasattr(tool, "model_dump") else tool)
    return result


def _convert_thinking_config(thinking: Any) -> dict[str, Any]:
    """Convert thinking config to Anthropic SDK format."""
    if isinstance(thinking, dict):
        return thinking
    return thinking.model_dump() if hasattr(thinking, "model_dump") else thinking


def _format_sse_event(event: Any) -> str:
    """Format an Anthropic SDK event as Anthropic SSE format."""
    event_type = event.type if hasattr(event, "type") else type(event).__name__

    if event_type == "message_start":
        payload = {
            "type": "message_start",
            "message": _serialize_event(event.message),
        }
    elif event_type == "content_block_start":
        payload = {
            "type": "content_block_start",
            "index": event.index,
            "content_block": _serialize_event(event.content_block),
        }
    elif event_type == "content_block_delta":
        delta_data = {}
        if hasattr(event, "delta"):
            delta_data = _serialize_event(event.delta)
        payload = {
            "type": "content_block_delta",
            "index": event.index,
            "delta": delta_data,
        }
    elif event_type == "message_delta":
        payload = {
            "type": "message_delta",
            "delta": _serialize_event(event.delta),
        }
        if hasattr(event, "usage"):
            payload["usage"] = _serialize_event(event.usage)
    elif event_type == "message_stop":
        payload = {"type": "message_stop"}
    else:
        return ""

    return f"data: {json.dumps(payload)}\n\n"


def _serialize_event(obj: Any) -> Any:
    """Serialize an event object to a dictionary."""
    if obj is None:
        return None
    if isinstance(obj, (dict, list, str, int, float, bool)):
        return obj
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return str(obj)
