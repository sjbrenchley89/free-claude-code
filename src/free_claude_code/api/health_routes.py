"""Health and diagnostics endpoints for MCP server integration."""

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException

from free_claude_code.core.version import package_version

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check() -> dict[str, object]:
    """Health check endpoint for MCP server and external monitors.

    Returns:
        {
            "status": "healthy",
            "version": "5.13.10",
            "timestamp": "2026-08-26T...",
        }
    """
    return {
        "status": "healthy",
        "version": package_version(),
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/config")
async def get_config(request) -> dict[str, object]:
    """Return current server configuration.

    This endpoint is used by the MCP server to inspect the proxy's
    routing configuration, including enabled providers and rules.
    """
    try:
        services = request.app.state.services
        settings = services.requests.current_settings()

        return {
            "version": package_version(),
            "provider_type": str(settings.provider_type)
            if hasattr(settings, "provider_type")
            else "unknown",
            "enabled_providers": _get_enabled_providers(settings),
            "fallback_enabled": getattr(settings, "fallback_enabled", False),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch config: {e}"
        ) from e


@router.get("/providers")
async def list_providers(request) -> dict[str, object]:
    """List all configured providers and their status.

    This endpoint is used by the MCP server to discover available
    providers and their operational status.
    """
    try:
        services = request.app.state.services
        settings = services.requests.current_settings()

        # Attempt to get provider status from the runtime
        # This is best-effort; the actual implementation depends on
        # how providers are managed in the runtime
        enabled_providers = _get_enabled_providers(settings)

        providers = [
            {
                "name": provider_name,
                "type": provider_name,
                "status": "unknown",  # Status would be checked from provider manager
                "configured": True,
            }
            for provider_name in enabled_providers
        ]

        return {
            "providers": providers,
            "count": len(providers),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list providers: {e}"
        ) from e


def _get_enabled_providers(settings) -> list[str]:
    """Extract list of enabled provider names from settings."""
    providers = []

    # Check common provider configuration attributes
    provider_configs = [
        ("openai_api_key", "openai"),
        ("anthropic_api_key", "anthropic"),
        ("nim_settings", "nvidia_nim"),
        ("google_credentials", "google"),
        ("azure_credentials", "azure"),
    ]

    for attr, name in provider_configs:
        if hasattr(settings, attr) and getattr(settings, attr):
            providers.append(name)

    # Check if a primary provider is set
    if hasattr(settings, "provider_type"):
        provider_type = str(settings.provider_type)
        if provider_type and provider_type not in providers:
            providers.append(provider_type)

    return providers if providers else ["unknown"]
