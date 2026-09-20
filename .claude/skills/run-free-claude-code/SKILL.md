---
name: run-free-claude-code
description: Build, start, and drive Free Claude Code (FCC) - the fcc-server FastAPI proxy and its browser-rendered Admin UI. Use when asked to run FCC, start the server, take a screenshot of the Admin UI, configure a provider, or confirm a change works in the real running app (not just its pytest/e2e suite).
---

Free Claude Code is a FastAPI server (`fcc-server`) with a
browser-rendered Admin UI at `/admin`. There is no `chromium-cli` binary
in this container, so driving the UI means launching the real server
then puppeting headless Chromium yourself. `driver.py` in this skill
directory does both: it owns one `fcc-server` subprocess and one
Playwright browser/page, and executes newline-delimited commands piped
over stdin (same shape as `chromium-cli`'s REPL). All paths below are
relative to the repo root.

## Prerequisites

Already satisfied by the project's own `uv sync` + Playwright install
(this container had both). On a fresh machine:

```bash
uv sync
uv run playwright install chromium
```

## Run (agent path)

Pipe commands to the driver. It starts `fcc-server` in an isolated
`HOME` (so it never touches your real `~/.fcc` config or provider
keys), waits for `/health`, then drives the Admin UI:

```bash
uv run python .claude/skills/run-free-claude-code/driver.py <<'EOF'
start-server 8090 /tmp/fcc-driver-home
open
screenshot 01_home
nav model_config
screenshot 02_model_config
nav providers
configure NVIDIA NIM
fill NVIDIA_NIM_API_KEY sk-test-smoke-1234
apply
screenshot 03_after_apply
console
quit
EOF
```

Screenshots land in `.claude/skills/run-free-claude-code/screenshots/`.
Verified in this container: `01_home.png` shows the full Providers
catalog; after `configure`/`fill`/`apply`, NVIDIA NIM's badge flips
from `MISSING KEY` to `CONFIGURED` and the value is written to
`/tmp/fcc-driver-home/.fcc/.env` (`NVIDIA_NIM_API_KEY=...`) - the
whole config round-trip actually works, not just the page rendering.

| command | what it does |
|---|---|
| `start-server <port> <home-dir>` | Launches `uv run fcc-server` with an isolated `HOME`, `FCC_OPEN_BROWSER=false`, `PROXY_AUTH_ENABLED=false`; blocks until `/health` responds (30s timeout) |
| `stop-server` | Terminates the server subprocess |
| `open [url]` | Launches Chromium (once) and navigates; defaults to `http://127.0.0.1:<port>/admin` from `start-server` |
| `nav <view>` | Clicks the sidebar tab: `providers`, `model_config`, `messaging`, or `chat` |
| `screenshot <name>` | Full-page screenshot to `screenshots/<name>.png` |
| `configure <provider display name>` | Clicks the `Configure` button inside the provider card matching that text, e.g. `configure NVIDIA NIM` |
| `fill <ENV_VAR_KEY> <value>` | Fills that field by its env var name (see Gotchas - not by visible label) |
| `apply` | Clicks `Apply`, waits for the POST response, reports whether the "unsaved change" bar is still showing |
| `console` | Prints any browser console errors collected so far |
| `quit` | Closes the browser and stops the server |

Lines starting with `#` are comments; blank lines are skipped.

## Direct invocation (most PRs need only this)

Nearly all FCC changes are in provider adapters, protocol translation,
or config/settings - not the Admin UI. For those, skip the browser
entirely:

```bash
uv run pytest tests/ -x -q          # unit + API contract tests
uv run pytest e2e/ -x -q            # Admin UI tests (own isolated server, real Playwright)
uv run python -c "from free_claude_code.config.loader import get_settings; print(get_settings().model)"
```

Reach for `driver.py` only when the change touches the Admin UI's
markup/JS/wiring itself.

## Run (human path)

```bash
uv run fcc-server
```

Prints the Admin UI URL (default `http://127.0.0.1:8082/admin`) and
blocks in the foreground; `Ctrl-C` to stop. Useless in this headless
container - use the agent path above instead.

## Test

```bash
uv run pytest tests/ -x -q          # unit/API contracts
uv run pytest e2e/ -x -q            # Admin UI, Playwright, own isolated server per test
```

Verified in this container: `uv run pytest e2e/test_admin_providers.py -x -q` -> 6 passed in ~12s.

## Gotchas

- **Nav items are `<button data-view="...">`, not `<a>` links.** `get_by_role("link", ...)` times out silently for 30s. Use `button[data-view="providers|model_config|messaging|chat"]`.
- **Don't name a script `inspect.py`.** It shadows Python's stdlib `inspect` module, which `playwright.sync_api` imports transitively - you get a baffling `ImportError: cannot import name 'sync_playwright' from partially initialized module` that has nothing to do with Playwright itself.
- **Address provider key fields by their env var name (`data-key` attribute / `#field-<ENV_VAR>` id), not visible label text.** Each field's visible label text ("NVIDIA NIM API Key") also appears in an adjacent `DEFAULT` badge and an aria-label, so a Playwright `text=` locator resolves to multiple elements (strict-mode violation) or the wrong one. `input[data-key="NVIDIA_NIM_API_KEY"]` is unambiguous - the env var name is printed in each provider card's meta line, so you can read it straight off the Providers screenshot.
- **The `.provider-card` div and its inner `input` share the same `data-key`.** Scope with `input[data-key="..."]`, not the bare `[data-key="..."]` attribute selector, or you hit a two-element strict-mode violation.
- **`Apply` starts disabled** (`id="applyButton"`, `disabled`) and only enables once a field's `input` event fires a dirty-check. If you click it before that (e.g. because a prior `fill` silently failed) Playwright's default actionability retry burns the full 30s timeout before failing - `driver.py`'s `apply` command waits for `:not([disabled])` first (5s timeout) so a broken `fill` fails fast and legibly instead.
- **The "unsaved change" bar doesn't clear on a fixed `sleep` after clicking Apply.** The save is an async POST; wait for that response (`page.expect_response`) before asserting the bar is gone, or you'll get a false "still unsaved" read on a save that actually succeeded.
- **Isolate `HOME`.** `fcc-server` reads/writes `~/.fcc/.env` for all provider config. Point `HOME` at a scratch directory (as `driver.py`'s `start-server` does) so driving the Admin UI never touches your real provider keys.
