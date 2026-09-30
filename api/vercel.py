"""Vercel serverless entrypoint for Free Claude Code."""

from free_claude_code.config.loader import get_settings
from free_claude_code.runtime.bootstrap import build_asgi_app

# Load settings from environment (works with Vercel env vars)
settings = get_settings()

# Build and export the ASGI app for Vercel
app = build_asgi_app(settings)
