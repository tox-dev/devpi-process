from __future__ import annotations

import secrets
import socket
import string
import sys
import sysconfig
from contextlib import closing
from logging import getLogger
from pathlib import Path
from subprocess import PIPE, Popen  # ruff:ignore[suspicious-subprocess-import]  # no shell, argument lists only
from threading import Thread
from typing import IO, TYPE_CHECKING, cast

from ._command import check_call
from ._index import Index

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence
    from types import TracebackType
    from typing import Self


class IndexServer:
    """
    A PyPI index server locally.

    :ivar host: name the server is reached at, always localhost
    :ivar port: free TCP port the server listens on, picked when the object is created
    """

    def __init__(
        self,
        path: Path,
        # Preserve the public positional argument.
        with_root_pypi: bool = False,  # ruff:ignore[boolean-type-hint-positional-argument, boolean-default-value-positional-argument]
        start_args: Sequence[str] | None = None,
    ) -> None:
        """
        Create the local index server.

        :param path: the path where to host files
        :param with_root_pypi: access to upstream PyPI
        :param start_args: additional arguments to start the server
        """
        self.path = path
        self._with_root_pypi = with_root_pypi
        self._start_args: Sequence[str] = [] if start_args is None else start_args

        self.host = "localhost"
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as socket_handler:
            socket_handler.bind(("", 0))  # devpi can bind to any IPv4 interface via start_args
            self.port = cast("int", socket_handler.getsockname()[1])
        self._passwd = "".join(secrets.choice(string.ascii_letters) for _ in range(8))

        scripts_dir = sysconfig.get_path("scripts")
        if scripts_dir is None:
            msg = "could not get scripts folder of host interpreter"
            raise RuntimeError(msg)

        def _exe(name: str) -> str:
            return str(Path(scripts_dir) / f"{name}{'.exe' if sys.platform == 'win32' else ''}")

        self._init: str = _exe("devpi-init")
        self._server: str = _exe("devpi-server")
        self._client: str = _exe("devpi")

        self._server_dir = self.path / "server"
        self._client_dir = self.path / "client"
        self._indexes: dict[str, Index] = {}
        self._process: Popen[str] | None = None
        self._has_use = False
        self._stdout_drain: Thread | None = None

    def __enter__(self) -> Self:
        """Start the index server."""
        try:
            self._create_and_start_server()
            self._setup_client()
        except BaseException:
            self.__exit__(None, None, None)
            raise
        return self

    def _create_and_start_server(self) -> None:
        self._server_dir.mkdir(exist_ok=True)
        server_at = str(self._server_dir)
        # 1. create the server
        cmd = [self._init, "--serverdir", server_at]
        cmd.extend(("--role", "standalone", "--root-passwd", self._passwd))
        if self._with_root_pypi is False:
            cmd.append("--no-root-pypi")
        check_call(cmd)
        # 2. start the server
        cmd = [self._server, "--serverdir", server_at, "--port", str(self.port)]
        cmd.extend(self._start_args)
        self._process = Popen(cmd, stdout=PIPE, universal_newlines=True)  # ruff:ignore[subprocess-without-shell-equals-true]  # no shell, argument list only
        stdout = self._drain_stdout()
        for line in stdout:
            if "serving at url" in line:

                def _keep_draining() -> None:
                    for _ in stdout:
                        pass

                # important to keep draining the stdout, otherwise once the buffer is full Windows blocks the process
                self._stdout_drain = Thread(target=_keep_draining, name="tox-test-stdout-drain")
                self._stdout_drain.start()
                break
        else:
            msg = f"devpi server at {self._server_dir} exited before it was ready"
            raise RuntimeError(msg)

    def _drain_stdout(self) -> Iterator[str]:
        process = cast("Popen[str]", self._process)
        stdout = cast("IO[str]", process.stdout)
        while True:
            if process.poll() is not None:
                getLogger(__name__).error("devpi server with pid %s at %s died", process.pid, self._server_dir)
                break
            yield stdout.readline()

    def _setup_client(self) -> None:
        self._client_dir.mkdir(exist_ok=True)
        base = ["--clientdir", str(self._client_dir)]
        check_call([self._client, "use", *base, self.url])
        check_call([self._client, "login", *base, self.user, "--password", self._passwd])

    @property
    def url(self) -> str:
        """URL to the index server."""
        return f"http://{self.host}:{self.port}"

    @property
    def user(self) -> str:
        """Username of the index server."""
        return "root"

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """
        Stop the index server.

        :param exc_type: type of the exception leaving the block, or None
        :param exc_val: the exception leaving the block, or None
        :param exc_tb: traceback of that exception, or None
        """
        if self._process is not None:
            self._process.terminate()
        if self._stdout_drain is not None and self._stdout_drain.is_alive():
            self._stdout_drain.join()

    def __repr__(self) -> str:
        """Return the repr of the index server."""
        return f"{self.__class__.__name__}(url={self.url}, indexes={list(self._indexes)})"

    def create_index(self, name: str, *args: str) -> Index:
        """
        Create an index on the server.

        :param name: with name
        :param args: additional arguments
        :returns: the created index
        :raises ValueError: when an index with this name already exists
        """
        if name in self._indexes:
            msg = f"index {name} already exists"
            raise ValueError(msg)
        base = [self._client, "--clientdir", str(self._client_dir)]
        check_call([*base, "index", "-c", name, *args])
        index = Index(f"{self.url}/{self.user}", name, self.user, base)
        self._indexes[name] = index
        return index


__all__ = [
    "IndexServer",
]
