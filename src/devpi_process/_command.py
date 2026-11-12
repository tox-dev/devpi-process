from __future__ import annotations

from subprocess import run  # ruff:ignore[suspicious-subprocess-import] command uses an argument list


def check_call(cmd: list[str]) -> None:
    run(cmd, check=True, capture_output=True)  # ruff:ignore[subprocess-without-shell-equals-true] argument list


__all__ = [
    "check_call",
]
