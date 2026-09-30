# FCC-server on Railway

Deploy the repository's `main` branch with the Railpack builder.
[`deploy/railway-service.json`](../deploy/railway-service.json) records the
production service settings. Apply those fields through Railway's service
settings or the Railway `update-service` tool, with the intended project,
environment, and service IDs. This JSON profile is a reference for applying
settings; Railway does not automatically import it. `railpack.json` supplies
the same startup command during image builds. The build installs locked
production dependencies; startup runs the standard FCC server supervisor after
restoring authentication from the Railway secret.

Service-level `railway.json` / `railway.toml` config is deprecated by Railway.
Do not select a custom config-file path for this setup. Project-level
Infrastructure as Code can be imported separately with `railway config pull`
and reviewed with `railway config plan` before applying it.

Set these service variables:

| Variable | Value |
| --- | --- |
| `RAILPACK_PYTHON_VERSION` | `3.14.7` |
| `SETUPTOOLS_SCM_PRETEND_VERSION` | `6.5.11` |
| `FCC_DEPLOY_AUTH_TOKEN` | A random secret of at least 32 printable ASCII characters, without spaces |
| `HOST` | `0.0.0.0` |
| `PORT` | `8082` |
| `PROXY_AUTH_ENABLED` | `true` |
| `FCC_OPEN_BROWSER` | `false` |

Generate the token locally with `python -c 'import secrets; print(secrets.token_urlsafe(48))'`
and save it as a Railway secret. Keep it out of source control and logs. Supply
the same token to API clients using `Authorization: Bearer <token>` or
`x-api-key: <token>`. To rotate it, update `FCC_DEPLOY_AUTH_TOKEN` and redeploy.
FCC deliberately uses a managed auth token, so setting only
`ANTHROPIC_AUTH_TOKEN` in the process environment does not replace this bootstrap.

The version override supplies package metadata when Railway builds a checkout
without `.git`. Update it and the Python version when upgrading FCC. Configure
provider credentials and model selections as Railway service variables using
the names in the main README.

Route the public HTTPS domain to port `8082`. `/health` is unauthenticated for
Railway readiness checks; API routes require the token. Admin routes require a
loopback connection and return `403` over the public domain. The service stays
awake, uses a 120-second readiness timeout, and retries failed processes up to
three times.

Use one replica: FCC stores configuration and session state under `~/.fcc`,
including SQLite databases. The current Railway service has no persistent
volume, so session state and changes stored only in managed configuration are
lost when a container is replaced. Railway variables, including the auth
token, are restored at startup. For durable sessions, attach a volume at the
container's actual `~/.fcc` directory before relying on stored session state.
