from __future__ import annotations

from subprocess import run  # ruff:ignore[suspicious-subprocess-import]
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


class Index:
    """Index."""

    def __init__(self, base_url: str, name: str, user: str, client_cmd_base: list[str]) -> None:
        """
        Create index.

        :param base_url: base url
        :param name: name for the index server
        :param user: the username to use
        :param client_cmd_base:
        """
        self._client_cmd_base = client_cmd_base
        self._server_url = base_url
        self.name = name
        self.user = user

    def __repr__(self) -> str:
        """:return: repr of the index"""
        return f"{self.__class__.__name__}(url={self.url})"

    @property
    def url(self) -> str:
        """The URL to the index server."""
        return f"{self._server_url}/{self.name}/+simple/"

    def use(self) -> None:
        """Use this index server."""
        _check_call([*self._client_cmd_base, "use", f"{self.user}/{self.name}"])

    def upload(self, *files: Path) -> None:
        """
        Upload packages to the index.

        :param files: the files to upload
        """
        _check_call(self._client_cmd_base + ["upload", "--index", self.name] + [str(i) for i in files])


def _check_call(cmd: list[str]) -> None:
    run(cmd, check=True, capture_output=True)  # ruff:ignore[subprocess-without-shell-equals-true]


__all__ = [
    "Index",
]
