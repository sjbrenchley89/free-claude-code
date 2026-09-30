"""Authenticated, non-interactive startup for a cloud FCC server."""

import os
import re

from free_claude_code.config.env_files import ANTHROPIC_AUTH_TOKEN_ENV
from free_claude_code.config.loader import (
    ManagedConfigStore,
    clear_settings_cache,
    compose_settings_snapshot,
)

from .entrypoints import serve


def configure_cloud() -> None:
    """Restore the deployment token before validating the network listener."""
    env = dict(os.environ)
    token = env.get("FCC_DEPLOY_AUTH_TOKEN", "")
    if re.fullmatch(r"[!-~]{32,}", token) is None:
        raise ValueError(
            "FCC_DEPLOY_AUTH_TOKEN must contain at least 32 printable ASCII "
            "characters without spaces."
        )

    env.setdefault("HOST", "0.0.0.0")
    env.setdefault("PORT", "8082")
    env.setdefault("PROXY_AUTH_ENABLED", "true")
    env.setdefault("FCC_OPEN_BROWSER", "false")

    store = ManagedConfigStore()
    store.initialize(env)
    # The managed token can still be the local default on a fresh container.
    # Read using a safe loopback override, then validate the prospective token
    # with the real deployment environment before changing managed storage.
    managed = store.read(
        env | {"HOST": "127.0.0.1", "PROXY_AUTH_ENABLED": "false"}
    ).managed
    values = dict(managed)
    values[ANTHROPIC_AUTH_TOKEN_ENV] = token
    try:
        settings = compose_settings_snapshot(values, env).settings
    except ValueError:
        # Pydantic model errors can include the complete input, including secrets.
        raise ValueError(
            "Invalid cloud settings; check the service variables."
        ) from None
    if not settings.proxy_auth_enabled:
        raise ValueError("Cloud startup requires PROXY_AUTH_ENABLED=true.")
    if not 1 <= settings.port <= 65535:
        raise ValueError("PORT must be between 1 and 65535.")
    if settings.open_admin_browser:
        raise ValueError("Cloud startup requires FCC_OPEN_BROWSER=false.")
    if values != managed:
        store.commit(values)
    os.environ.update(env)
    clear_settings_cache()


def main() -> None:
    """Prepare managed authentication and run the standard server supervisor."""
    try:
        configure_cloud()
    except ValueError, OSError, TimeoutError:
        raise SystemExit(
            "FCC cloud configuration failed. Check FCC_DEPLOY_AUTH_TOKEN, "
            "HOST, PORT, PROXY_AUTH_ENABLED, FCC_OPEN_BROWSER and config storage."
        ) from None
    serve(())


if __name__ == "__main__":
    main()
