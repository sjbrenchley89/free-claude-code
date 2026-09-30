"""Server bind configuration keeps local clients and Admin reachable."""

import pytest
from pydantic import ValidationError

from free_claude_code.config.loader import compose_settings_snapshot
from free_claude_code.config.server_urls import local_admin_url, local_proxy_root_url
from free_claude_code.config.settings import Settings


@pytest.mark.parametrize("host", ["0.0.0.0", "::", "[::]"])
def test_network_bind_requires_authentication_and_custom_token(host):
    with pytest.raises(ValidationError, match="PROXY_AUTH_ENABLED=true"):
        Settings(HOST=host, ANTHROPIC_AUTH_TOKEN="custom-token")
    with pytest.raises(ValidationError, match="custom ANTHROPIC_AUTH_TOKEN"):
        Settings(HOST=host, PROXY_AUTH_ENABLED=True)


@pytest.mark.parametrize(
    ("host", "expected"),
    [
        ("127.0.0.1", "127.0.0.1"),
        ("127.0.0.2", "127.0.0.2"),
        ("localhost", "localhost"),
        ("LOCALHOST", "localhost"),
        ("::1", "[::1]"),
        ("[::1]", "[::1]"),
        ("0.0.0.0", "127.0.0.1"),
        ("::", "[::1]"),
        ("[::]", "[::1]"),
    ],
)
def test_local_client_urls_match_bind_address_family(host, expected):
    settings = Settings(
        HOST=host, PROXY_AUTH_ENABLED=True, ANTHROPIC_AUTH_TOKEN="custom-token"
    )
    assert local_proxy_root_url(settings) == f"http://{expected}:8082"
    assert local_admin_url(settings) == f"http://{expected}:8082/admin"
    assert "[" not in settings.host


@pytest.mark.parametrize("host", ["192.168.1.10", "2001:db8::1"])
def test_specific_network_bind_rejected_before_admin_becomes_unreachable(host):
    with pytest.raises(ValidationError, match="loopback listener"):
        Settings(
            HOST=host, PROXY_AUTH_ENABLED=True, ANTHROPIC_AUTH_TOKEN="custom-token"
        )


@pytest.mark.parametrize(
    "host", ["example.com", "[::", "http://localhost", "::%lo", "[::%1]"]
)
def test_invalid_bind_host_rejected(host):
    with pytest.raises(ValidationError, match="HOST must"):
        Settings(HOST=host)


def test_process_override_cannot_disable_auth_on_managed_network_bind():
    managed = {
        "HOST": "0.0.0.0",
        "PROXY_AUTH_ENABLED": "true",
        "ANTHROPIC_AUTH_TOKEN": "custom-token",
    }
    with pytest.raises(ValidationError, match="PROXY_AUTH_ENABLED=true"):
        compose_settings_snapshot(managed, {"PROXY_AUTH_ENABLED": "false"})
    assert compose_settings_snapshot(managed, {}).settings.proxy_auth_enabled
