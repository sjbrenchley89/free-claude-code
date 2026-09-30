"""Cloud startup must restore authentication without exposing invalid settings."""

import json
import os
from pathlib import Path

import pytest

from free_claude_code.cli import cloud
from free_claude_code.config.loader import ManagedConfigStore, get_settings
from free_claude_code.config.paths import managed_env_path

TOKEN = "test-cloud-token-" + "a" * 48


@pytest.fixture(autouse=True)
def cloud_environment(monkeypatch):
    # Bootstrap installs process defaults directly; restore the whole mapping
    # so defaults created by a test cannot reach subsequent local-server tests.
    monkeypatch.setattr(os, "environ", os.environ.copy())
    for key in (
        "HOST",
        "PORT",
        "PROXY_AUTH_ENABLED",
        "FCC_OPEN_BROWSER",
        "FCC_DEPLOY_AUTH_TOKEN",
        "ANTHROPIC_AUTH_TOKEN",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("FCC_DEPLOY_AUTH_TOKEN", TOKEN)


def test_fresh_cloud_restores_managed_token_and_clears_cached_settings():
    assert get_settings().proxy_auth_token == "freecc"
    cloud.configure_cloud()
    settings = get_settings()
    assert settings.host == "0.0.0.0"
    assert settings.port == 8082
    assert settings.proxy_auth_enabled
    assert settings.proxy_auth_token == TOKEN
    assert not settings.open_admin_browser
    if os.name != "nt":
        assert managed_env_path().stat().st_mode & 0o777 == 0o600


def test_rotation_preserves_provider_config_and_repeated_start_does_not_write(
    monkeypatch,
):
    store = ManagedConfigStore()
    store.initialize()
    values = dict(store.read().managed)
    values["ANTHROPIC_AUTH_TOKEN"] = "old-managed-token"
    values["OPENAI_API_KEY"] = "existing-provider-key"
    values["UNKNOWN_PRIVATE"] = "preserved-value"
    store.commit(values)
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "ignored-process-token")
    monkeypatch.setenv("PORT", "8123")
    cloud.configure_cloud()
    snapshot = store.read()
    assert snapshot.settings.proxy_auth_token == TOKEN
    assert snapshot.settings.port == 8123
    assert snapshot.managed["OPENAI_API_KEY"] == "existing-provider-key"
    assert snapshot.managed["UNKNOWN_PRIVATE"] == "preserved-value"
    before = store.path.read_bytes(), store.path.stat().st_mtime_ns
    cloud.configure_cloud()
    assert (store.path.read_bytes(), store.path.stat().st_mtime_ns) == before


@pytest.mark.parametrize("token", ["", "freecc", "a" * 31, "a" * 32 + "\n", "a b" * 20])
def test_invalid_token_fails_before_creating_managed_config(monkeypatch, token):
    monkeypatch.setenv("FCC_DEPLOY_AUTH_TOKEN", token)
    with pytest.raises(ValueError, match="FCC_DEPLOY_AUTH_TOKEN"):
        cloud.configure_cloud()
    assert not managed_env_path().exists()


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("PROXY_AUTH_ENABLED", "false"),
        ("FCC_OPEN_BROWSER", "true"),
        ("HOST", "192.168.1.10"),
        ("PORT", "0"),
        ("PORT", "65536"),
        ("PORT", "invalid-port"),
    ],
)
def test_invalid_service_settings_preserve_existing_managed_token(
    monkeypatch, key, value
):
    store = ManagedConfigStore()
    store.initialize()
    before = store.path.read_bytes()
    monkeypatch.setenv(key, value)
    with pytest.raises(ValueError):
        cloud.configure_cloud()
    assert store.path.read_bytes() == before


def test_main_hides_validation_inputs_and_does_not_start_server(monkeypatch):
    monkeypatch.setenv("PROXY_AUTH_ENABLED", "false")
    calls = []
    monkeypatch.setattr(cloud, "serve", lambda args: calls.append(args))
    with pytest.raises(SystemExit) as error:
        cloud.main()
    assert TOKEN not in str(error.value)
    assert not calls


def test_main_starts_standard_server_after_bootstrap(monkeypatch):
    tokens = []
    monkeypatch.setattr(
        cloud, "serve", lambda args: tokens.append(get_settings().proxy_auth_token)
    )
    cloud.main()
    assert tokens == [TOKEN]


def test_railway_profile_and_railpack_start_same_bootstrap():
    root = Path(__file__).resolve().parents[2]
    railway = json.loads(
        (root / "deploy/railway-service.json").read_text(encoding="utf-8")
    )
    railpack = json.loads((root / "railpack.json").read_text(encoding="utf-8"))
    assert railway["startCommand"] == railpack["deploy"]["startCommand"]
    assert railway["buildCommand"] == "uv sync --locked --no-dev"
