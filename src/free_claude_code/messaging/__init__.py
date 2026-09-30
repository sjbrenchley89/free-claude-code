"""Platform-agnostic messaging layer."""

from __future__ import annotations
from .managed_protocols import (
    ManagedClaudeSessionManagerProtocol,
    ManagedClaudeSessionProtocol,
)
from .models import IncomingMessage, MessageScope
from .platforms.ports import OutboundMessenger

__all__ = [
    "IncomingMessage",
    "ManagedClaudeSessionManagerProtocol",
    "ManagedClaudeSessionProtocol",
    "MessageScope",
    "OutboundMessenger",
]
