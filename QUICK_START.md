# Setup And Usage Guide

This guide gets Free Claude Code (FCC) running and connects a coding agent to
your configured models.

## Choose An Install Method

### Recommended: installer

On macOS or Linux:

```bash
curl -fsSL "https://raw.githubusercontent.com/Alishahryar1/free-claude-code/main/scripts/install.sh" | sh
```

On Windows PowerShell:

```powershell
& ([scriptblock]::Create((irm "https://raw.githubusercontent.com/Alishahryar1/free-claude-code/main/scripts/install.ps1")))
```

Choose at least one coding agent during installation. Run the same command
again later to update FCC.

### From source with uv

Requirements: Python 3.14 and uv 0.11.16 or newer.

```bash
git clone https://github.com/Alishahryar1/free-claude-code.git
cd free-claude-code
uv sync
uv run fcc-server
```

### Docker Compose

```bash
git clone https://github.com/Alishahryar1/free-claude-code.git
cd free-claude-code
cp .env.example .env.production
docker compose up -d fcc-server
```

Docker Compose serves FCC on `http://localhost:8082`. The Prometheus and
Grafana services are optional:

```bash
docker compose up -d prometheus grafana
```

## Configure A Provider

1. Open the Admin UI at `http://localhost:8082` for Docker, or use the URL
  printed by `fcc-server`.
2. Open **Providers** and choose a provider.
3. Add the provider API key or local endpoint. Never commit keys to git.
4. Choose a model in **Model Config**, or enter a model as
  `provider/model-id`.
5. Optionally add ordered **Fallback Models**.
6. Click **Apply**, then use **Check** to verify the provider.

The provider catalog and key links are in [README.md](./README.md#choose-a-provider).
For Docker, edit `.env.production` and restart the service when changing
environment variables:

```bash
docker compose restart fcc-server
```

The example configuration is in [.env.example](./.env.example). Only the
variables required by your selected provider need to be set. The default
model is NVIDIA NIM, so configure `NVIDIA_NIM_API_KEY` or select another
provider before starting a request.

## Start And Use FCC

With the installer or a source install, start the server first:

```bash
fcc-server
```

Keep that terminal open on Linux. Then launch one of the installed clients in
another terminal:

```bash
fcc-claude
fcc-codex
fcc-pi
fcc-opencode
fcc-cline
fcc-hermes
fcc-dsh
fcc-grok
fcc-muse
fcc-aider
```

Run the command from the project directory you want the agent to work in.
The launchers configure the selected client to use FCC and preserve the
client's normal tools and workflow.

## Docker Operations

```bash
docker compose ps
docker compose logs -f fcc-server
curl http://localhost:8082/health
docker compose restart fcc-server
docker compose down
```

To rebuild after changing source or the Dockerfile:

```bash
docker compose build fcc-server
docker compose up -d fcc-server
```

## Troubleshooting

### Admin UI does not open

Check the server output or Docker logs for the actual port:

```bash
docker compose logs fcc-server
curl http://localhost:8082/health
```

### Provider check fails

Confirm that the key is valid, the provider prefix matches the selected
model, and the model ID is supported by that provider. For local providers,
start the local server first and verify its base URL in Admin.

### A coding agent command is missing

Run the installer again and select that agent, or install the project entry
points from source with `uv sync`. Check the installed commands with:

```bash
command -v fcc-server fcc-claude fcc-codex
```

### Reset Docker state

This removes FCC containers and their named monitoring volumes:

```bash
docker compose down -v
docker compose up -d fcc-server
```

## More Documentation

- [Main README and provider catalog](./README.md)
- [Docker deployment guide](./DOCKER_DEPLOYMENT_GUIDE.md)
- [Environment variable reference](./ENVIRONMENT_SETUP.md)
- [Deployment guide](./DEPLOYMENT.md)

