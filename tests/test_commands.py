from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from levelupdiag_core.commands import format_command, run_cmd
from levelupdiag_core.verdicts import FAIL, INFRA_ERROR, PASS


def python_cmd(source: str) -> list[str]:
    return [sys.executable, "-c", source]


def test_run_cmd_pass_and_captures_metadata(tmp_path: Path) -> None:
    result = run_cmd(
        python_cmd("print('hello from pass')"),
        cwd=tmp_path,
        timeout=5,
    )

    assert result.verdict == PASS
    assert result.exit_code == 0
    assert result.command[0] == sys.executable
    assert result.cwd == str(tmp_path.resolve())
    assert "hello from pass" in result.output_tail
    assert result.started_at
    assert result.ended_at
    assert result.duration_seconds >= 0
    assert result.error is None


def test_run_cmd_nonzero_is_fail(tmp_path: Path) -> None:
    result = run_cmd(
        python_cmd("import sys; print('expected failure'); sys.exit(7)"),
        cwd=tmp_path,
        timeout=5,
    )

    assert result.verdict == FAIL
    assert result.exit_code == 7
    assert "expected failure" in result.output_tail
    assert result.error is None


def test_run_cmd_missing_executable_is_infra_error(tmp_path: Path) -> None:
    result = run_cmd(
        ["levelupdiag-koali-command-that-does-not-exist-8fc3"],
        cwd=tmp_path,
        timeout=5,
    )

    assert result.verdict == INFRA_ERROR
    assert result.exit_code is None
    assert result.error is not None
    assert result.error in result.output_tail


def test_run_cmd_timeout_is_infra_error_and_keeps_available_output(tmp_path: Path) -> None:
    result = run_cmd(
        python_cmd(
            "import time; print('before timeout', flush=True); time.sleep(5)"
        ),
        cwd=tmp_path,
        timeout=0.15,
        name="timeout-probe",
    )

    assert result.verdict == INFRA_ERROR
    assert result.exit_code is None
    assert result.error is not None
    assert "timed out" in result.error.lower()
    assert "timeout-probe" in result.output_tail


def test_run_cmd_requires_argument_sequence(tmp_path: Path) -> None:
    with pytest.raises(TypeError):
        run_cmd("echo unsafe string", cwd=tmp_path)  # type: ignore[arg-type]


def test_run_cmd_bounds_output_tail(tmp_path: Path) -> None:
    result = run_cmd(
        python_cmd("print('x' * 1000)"),
        cwd=tmp_path,
        tail_chars=64,
    )
    assert result.verdict == PASS
    assert len(result.output_tail) <= 64


def test_run_cmd_does_not_embed_environment_in_result(tmp_path: Path) -> None:
    secret = "LEVELUPDIAG_TEST_SECRET_DO_NOT_LOG"
    result = run_cmd(
        python_cmd("print('clean')"),
        cwd=tmp_path,
        env={**os.environ, secret: "sensitive-value"},
    )

    assert result.verdict == PASS
    assert secret not in result.output_tail
    assert "sensitive-value" not in result.output_tail
    assert "sensitive-value" not in format_command(result.command)


def test_launch_console_uses_argument_sequence_and_shell_false(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import levelupdiag_core.commands as commands

    captured: dict[str, object] = {}

    class DummyProcess:
        pass

    def fake_popen(args, **kwargs):
        captured["args"] = args
        captured.update(kwargs)
        return DummyProcess()

    monkeypatch.setattr(commands.subprocess, "Popen", fake_popen)
    proc = commands.launch_console([sys.executable, "-V"], tmp_path, title="ignored safely")

    assert isinstance(proc, DummyProcess)
    assert captured["args"] == [sys.executable, "-V"]
    assert captured["cwd"] == str(tmp_path.resolve())
    assert captured["shell"] is False
