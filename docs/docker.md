# FCC-server with Docker

The Docker deployment files use the same authenticated startup module as
Railway. Docker and Railway deployments retain Python 3.14.7, locked production
dependencies, and the current FCC package metadata. The Dockerfile lives at
`deploy/docker/Dockerfile` so Railway continues using Railpack.

With Docker Compose installed, run from the repository root:

```sh
./scripts/docker-deploy.sh setup
./scripts/docker-deploy.sh build
./scripts/docker-deploy.sh start
./scripts/docker-deploy.sh test
```

Setup asks for a provider, model, API key and published host port. It writes a
private `.env` file and generates a random `FCC_DEPLOY_AUTH_TOKEN`. API clients
must send this token with `Authorization: Bearer <token>`; Anthropic message
routes also accept `x-api-key`. The helper refuses to replace an existing `.env`
unless `setup --force` is explicitly requested. Replacing it rotates the token
and provider settings; run `./scripts/docker-deploy.sh restart` afterward to
recreate the container with the new settings and keep its saved state.

Compose publishes port 8082 to loopback by default. To enable access from
another machine, set `FCC_PUBLISH_HOST=0.0.0.0` when starting Compose and put
HTTPS in front of the service. The server requires authentication even when
the published host port is loopback. Admin routes require loopback inside the
container and are unavailable through the published Docker port.

The `fcc-config` volume persists managed configuration, provider auth, logs,
and session state at `/home/app/.fcc`. `stop` and `down` keep this volume.
Do not remove it unless you intend to delete saved state. `logs`, `status`,
and `restart` expose the matching Compose operations.

For manual builds, use:

```sh
docker build -f deploy/docker/Dockerfile -t free-claude-code:local .
```

The image runs as an unprivileged user and requires `FCC_DEPLOY_AUTH_TOKEN` at
runtime. A build with no Git history uses `FCC_VERSION=6.5.11` for package
metadata. Update that build argument and the Python image when upgrading FCC.

If your build network uses a private certificate authority, supply its trusted
CA bundle with `--secret id=fcc_ca,src=/path/to/ca-bundle.pem`. BuildKit exposes
it only during dependency installation; the bundle is not stored in the image.
