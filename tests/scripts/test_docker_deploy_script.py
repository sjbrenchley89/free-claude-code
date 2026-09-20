import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _script() -> Path:
    return _repo_root() / "scripts" / "docker-deploy.sh"


def _shell_interpreter() -> str:
    sh = shutil.which("sh")
    if sh is None:
        pytest.skip("sh is not available on this platform")
    return sh


def _script_text() -> str:
    return _script().read_text(encoding="utf-8")


def _write_shim(path: Path, body: str) -> None:
    path.write_text("#!/bin/sh\n" + body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


@pytest.fixture
def project(tmp_path: Path) -> Path:
    root = tmp_path / "free-claude-code"
    (root / "scripts").mkdir(parents=True)
    shutil.copy(_script(), root / "scripts" / "docker-deploy.sh")
    (root / "scripts" / "docker-deploy.sh").chmod(0o755)
    shutil.copy(_repo_root() / "docker-compose.yml", root / "docker-compose.yml")
    shutil.copy(_repo_root() / "Dockerfile", root / "Dockerfile")
    return root


@pytest.fixture
def fake_bin(tmp_path: Path) -> tuple[str, Path]:
    """A PATH front with stubbed docker/curl that log their invocations."""
    bindir = tmp_path / "bin"
    bindir.mkdir()
    log = tmp_path / "calls.log"
    _write_shim(
        bindir / "docker",
        f'printf "docker %s\\n" "$*" >> "{log.as_posix()}"\n'
        'if [ "$1" = "compose" ] && [ "$2" = "version" ]; then exit 0; fi\n'
        "exit 0\n",
    )
    _write_shim(
        bindir / "curl",
        f'printf "curl %s\\n" "$*" >> "{log.as_posix()}"\n'
        'printf \'{"status":"healthy"}\'\n'
        "exit 0\n",
    )
    front = os.pathsep.join([str(bindir), os.environ.get("PATH", "")])
    return front, log


def _run(
    project: Path, path_front: str, *args: str, stdin: str = ""
) -> subprocess.CompletedProcess[str]:
    # Write stdin as bytes. Text mode rewrites "\n" to os.linesep, and on
    # Windows the resulting CR stays in the answers the shell's `read` returns,
    # which a real user typing at a terminal never sends.
    completed = subprocess.run(
        [_shell_interpreter(), str(project / "scripts" / "docker-deploy.sh"), *args],
        cwd=project,
        env={**os.environ, "PATH": path_front},
        input=stdin.encode("utf-8"),
        capture_output=True,
        check=False,
    )
    return subprocess.CompletedProcess(
        completed.args,
        completed.returncode,
        completed.stdout.decode("utf-8", "replace"),
        completed.stderr.decode("utf-8", "replace"),
    )


# ----------------------------- static contract -----------------------------


def test_script_exposes_documented_subcommands() -> None:
    text = _script_text()
    for sub in ("setup", "build", "start", "stop", "restart", "logs", "test", "down"):
        assert f"        {sub})" in text or f"        {sub} " in text
    assert "FCC_OPEN_BROWSER=false" in text
    assert "MODEL=" in text
    assert "docker compose version" in text
    assert "docker-compose" in text
    assert "/health" in text


def test_script_is_executable_in_git() -> None:
    entry = subprocess.run(
        ["git", "ls-files", "-s", "scripts/docker-deploy.sh"],
        cwd=_repo_root(),
        text=True,
        capture_output=True,
        check=True,
    ).stdout
    assert entry.startswith("100755"), entry


# ------------------------------- setup flow --------------------------------


def test_setup_writes_env_file(project: Path, fake_bin: tuple[str, Path]) -> None:
    front, _ = fake_bin
    # provider 1 (deepseek) -> accept default model -> no proxy auth -> default port
    result = _run(project, front, "setup", stdin="1\n\nsk-test-123\nN\n\n")
    assert result.returncode == 0, result.stderr

    env = (project / ".env").read_text(encoding="utf-8")
    assert "DEEPSEEK_API_KEY=sk-test-123" in env
    assert "MODEL=deepseek/deepseek-chat" in env
    assert "PROXY_AUTH_ENABLED=false" in env
    assert "FCC_OPEN_BROWSER=false" in env
    assert "PORT=8082" in env


def test_setup_enables_proxy_auth_with_generated_token(
    project: Path, fake_bin: tuple[str, Path]
) -> None:
    front, _ = fake_bin
    result = _run(project, front, "setup", stdin="1\n\nsk-test-123\ny\n\n")
    assert result.returncode == 0, result.stderr

    env = (project / ".env").read_text(encoding="utf-8")
    assert "PROXY_AUTH_ENABLED=true" in env
    token_line = next(
        line for line in env.splitlines() if line.startswith("ANTHROPIC_AUTH_TOKEN=")
    )
    assert token_line != "ANTHROPIC_AUTH_TOKEN=freecc"
    assert len(token_line.split("=", 1)[1]) >= 16


def test_setup_other_provider_prompts_for_env_var(
    project: Path, fake_bin: tuple[str, Path]
) -> None:
    front, _ = fake_bin
    result = _run(
        project,
        front,
        "setup",
        stdin="9\nmy_provider\nMY_PROVIDER_API_KEY\nmy_provider/some-model\nkey-xyz\nN\n\n",
    )
    assert result.returncode == 0, result.stderr
    env = (project / ".env").read_text(encoding="utf-8")
    assert "MY_PROVIDER_API_KEY=key-xyz" in env
    assert "MODEL=my_provider/some-model" in env


def test_setup_refuses_to_clobber_without_force(
    project: Path, fake_bin: tuple[str, Path]
) -> None:
    front, _ = fake_bin
    (project / ".env").write_text("EXISTING=1\n", encoding="utf-8")
    result = _run(project, front, "setup", stdin="1\n\nsk\nN\n\n")
    assert result.returncode != 0
    assert "already exists" in result.stderr
    assert (project / ".env").read_text(encoding="utf-8") == "EXISTING=1\n"


def test_setup_force_overwrites(project: Path, fake_bin: tuple[str, Path]) -> None:
    front, _ = fake_bin
    (project / ".env").write_text("EXISTING=1\n", encoding="utf-8")
    result = _run(project, front, "setup", "--force", stdin="1\n\nsk-new\nN\n\n")
    assert result.returncode == 0, result.stderr
    assert "DEEPSEEK_API_KEY=sk-new" in (project / ".env").read_text(encoding="utf-8")


# --------------------------- compose delegation ----------------------------


def test_build_requires_env_file(project: Path, fake_bin: tuple[str, Path]) -> None:
    front, _ = fake_bin
    result = _run(project, front, "build")
    assert result.returncode != 0
    assert "setup" in result.stderr


def test_build_invokes_compose_build(project: Path, fake_bin: tuple[str, Path]) -> None:
    front, log = fake_bin
    (project / ".env").write_text("MODEL=x/y\nPORT=8082\n", encoding="utf-8")
    result = _run(project, front, "build")
    assert result.returncode == 0, result.stderr
    assert "docker compose build" in log.read_text(encoding="utf-8")


def test_start_invokes_compose_up_and_polls_health(
    project: Path, fake_bin: tuple[str, Path]
) -> None:
    front, log = fake_bin
    (project / ".env").write_text("MODEL=x/y\nPORT=8199\n", encoding="utf-8")
    result = _run(project, front, "start")
    assert result.returncode == 0, result.stderr
    calls = log.read_text(encoding="utf-8")
    assert "docker compose up -d" in calls
    assert "http://localhost:8199/health" in calls


def test_logs_follows_compose_logs(project: Path, fake_bin: tuple[str, Path]) -> None:
    front, log = fake_bin
    (project / ".env").write_text("MODEL=x/y\n", encoding="utf-8")
    result = _run(project, front, "logs")
    assert result.returncode == 0, result.stderr
    assert "docker compose logs -f" in log.read_text(encoding="utf-8")


def test_unknown_subcommand_exits_with_usage(
    project: Path, fake_bin: tuple[str, Path]
) -> None:
    front, _ = fake_bin
    result = _run(project, front, "frobnicate")
    assert result.returncode == 2
    assert "unknown subcommand" in result.stderr
