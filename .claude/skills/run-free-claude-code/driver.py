"""REPL driver for launching and clicking through the FCC Admin UI.

Free Claude Code (FCC) is a FastAPI server (``fcc-server``) with a
browser-rendered Admin UI at ``/admin``. There is no ``chromium-cli`` binary
in this environment, so this script is a minimal from-scratch REPL that
plays the same role: it owns one server subprocess and one headless
Playwright browser/page, and executes newline-delimited commands piped
over stdin. See SKILL.md for the command reference and example sessions.

Run under ``uv run`` so the project's own Playwright + Chromium install is
used (``uv run playwright install chromium`` once, if not already done).
"""

import os
import shlex
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

SKILL_DIR = Path(__file__).resolve().parent
SCREENSHOT_DIR = SKILL_DIR / "screenshots"

NAV_VIEWS = {"providers", "model_config", "messaging", "chat"}


class Driver:
    def __init__(self) -> None:
        self.server_proc: subprocess.Popen | None = None
        self.server_port: int | None = None
        self.playwright = None
        self.browser = None
        self.page = None
        self.console_errors: list[str] = []

    # -- server lifecycle ------------------------------------------------

    def start_server(self, port: int, home_dir: str) -> None:
        if self.server_proc is not None:
            print("server already running")
            return
        Path(home_dir).mkdir(parents=True, exist_ok=True)
        env = {
            "HOME": home_dir,
            "USERPROFILE": home_dir,
            "PATH": subprocess.os.environ.get("PATH", ""),
            "FCC_OPEN_BROWSER": "false",
            "PROXY_AUTH_ENABLED": "false",
            "MESSAGING_PLATFORM": "none",
            "VOICE_NOTE_ENABLED": "false",
            "PORT": str(port),
        }
        self.server_proc = subprocess.Popen(
            ["uv", "run", "fcc-server"],
            cwd=SKILL_DIR.parent.parent.parent,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        self.server_port = port
        deadline = time.monotonic() + 30
        url = f"http://127.0.0.1:{port}/health"
        while time.monotonic() < deadline:
            if self.server_proc.poll() is not None:
                raise RuntimeError(
                    "fcc-server exited during startup:\n"
                    + (self.server_proc.stdout.read() or "")
                )
            try:
                urllib.request.urlopen(url, timeout=1)
                print(f"server healthy on port {port}")
                return
            except urllib.error.URLError, ConnectionError:
                time.sleep(0.3)
        raise TimeoutError("fcc-server did not become healthy within 30s")

    def stop_server(self) -> None:
        if self.server_proc is None:
            print("no server running")
            return
        self.server_proc.terminate()
        try:
            self.server_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.server_proc.kill()
            self.server_proc.wait(timeout=5)
        self.server_proc = None
        self.server_port = None
        print("server stopped")

    # -- browser lifecycle ------------------------------------------------

    def open(self, url: str | None) -> None:
        if url is None:
            if self.server_port is None:
                raise ValueError(
                    "no server running; pass an explicit url or start-server first"
                )
            url = f"http://127.0.0.1:{self.server_port}/admin"
        if self.playwright is None:
            self.playwright = sync_playwright().start()
            launch_kwargs: dict[str, str] = {}
            pinned_chromium = "/opt/pw-browsers/chromium"
            if os.path.exists(pinned_chromium):
                launch_kwargs["executable_path"] = pinned_chromium
            self.browser = self.playwright.chromium.launch(**launch_kwargs)
            self.page = self.browser.new_page(viewport={"width": 1280, "height": 900})
            self.page.on(
                "console",
                lambda msg: (
                    self.console_errors.append(msg.text)
                    if msg.type == "error"
                    else None
                ),
            )
        self.page.goto(url, wait_until="networkidle")
        print(f"opened {url} -- title: {self.page.title()}")

    def nav(self, view: str) -> None:
        if view not in NAV_VIEWS:
            raise ValueError(
                f"unknown view {view!r}; expected one of {sorted(NAV_VIEWS)}"
            )
        self.page.click(f'button[data-view="{view}"]')
        self.page.wait_for_timeout(300)
        print(f"navigated to {view}")

    def screenshot(self, name: str) -> None:
        SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
        path = SCREENSHOT_DIR / f"{name}.png"
        self.page.screenshot(path=str(path), full_page=True)
        print(f"screenshot saved to {path}")

    def configure(self, provider_text: str) -> None:
        card = self.page.locator(".provider-card", has_text=provider_text).first
        card.locator("button:has-text('Configure')").click()
        self.page.wait_for_timeout(300)
        print(f"clicked Configure for {provider_text!r}")

    def fill(self, env_var_key: str, value: str) -> None:
        # Fields are addressed by their env var name (e.g. NVIDIA_NIM_API_KEY),
        # shown in each provider card's .provider-meta text -- not by visible
        # label text, which collides with the adjacent "DEFAULT" badge and
        # matches multiple inputs under Playwright's text= locator.
        field = self.page.locator(f'input[data-key="{env_var_key}"]')
        field.fill(value)
        print(f"filled {env_var_key!r}")

    def apply(self) -> None:
        # Fail fast and clearly if nothing is dirty yet, instead of burning
        # Playwright's ~30s default actionability retry loop on a disabled button.
        self.page.wait_for_selector(
            "button:has-text('Apply'):not([disabled])", timeout=5_000
        )
        with self.page.expect_response(
            lambda r: r.request.method == "POST", timeout=10_000
        ):
            self.page.click("button:has-text('Apply')")
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(200)
        still_unsaved = self.page.is_visible("text=unsaved change")
        print(f"applied -- unsaved bar still visible: {still_unsaved}")

    def console(self) -> None:
        print(f"console errors ({len(self.console_errors)}):")
        for line in self.console_errors:
            print(f"  {line}")

    def quit(self) -> None:
        if self.browser is not None:
            self.browser.close()
            self.playwright.stop()
            self.browser = None
            self.playwright = None
        self.stop_server()


def main() -> None:
    driver = Driver()
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = shlex.split(line)
        cmd, args = parts[0], parts[1:]
        try:
            if cmd == "start-server":
                port = int(args[0]) if args else 8090
                home = args[1] if len(args) > 1 else "/tmp/fcc-driver-home"
                driver.start_server(port, home)
            elif cmd == "stop-server":
                driver.stop_server()
            elif cmd == "open":
                driver.open(args[0] if args else None)
            elif cmd == "nav":
                driver.nav(args[0])
            elif cmd == "screenshot":
                driver.screenshot(args[0] if args else "screenshot")
            elif cmd == "configure":
                driver.configure(" ".join(args))
            elif cmd == "fill":
                driver.fill(args[0], " ".join(args[1:]))
            elif cmd == "apply":
                driver.apply()
            elif cmd == "console":
                driver.console()
            elif cmd == "quit":
                driver.quit()
                return
            else:
                print(f"unknown command: {cmd}")
        except Exception as exc:
            print(f"error running {line!r}: {exc}")
    driver.quit()


if __name__ == "__main__":
    main()
