"""Devpi PyPI to test with."""  # simplint: ignore[unused-dependency]  # Provide the devpi commands it runs.

from __future__ import annotations

import secrets  # simplint: ignore[init-module-content]  # Public classes are defined here.
import socket  # simplint: ignore[init-module-content]  # Public classes are defined here.
import string  # simplint: ignore[init-module-content]  # Public classes are defined here.
import sys  # simplint: ignore[init-module-content]  # Public classes are defined here.
import sysconfig  # simplint: ignore[init-module-content]  # Public classes are defined here.
from contextlib import closing  # simplint: ignore[init-module-content]  # Public classes are defined here.
from logging import getLogger  # simplint: ignore[init-module-content]  # Public classes are defined here.
from pathlib import Path  # simplint: ignore[init-module-content]  # Public classes are defined here.
from subprocess import PIPE, Popen, run  # ruff:ignore[suspicious-subprocess-import]  # simplint: ignore[init-module-content]  # Public classes are defined here.
from threading import Thread  # simplint: ignore[init-module-content]  # Public classes are defined here.
from typing import IO, TYPE_CHECKING, cast  # simplint: ignore[init-module-content]  # Public classes are defined here.

from ._version import __version__

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence
    from types import TracebackType
    from typing import Self


class Index:  # ruff:ignore[non-empty-init-module]  # simplint: ignore[definition-before-use]  # Original public path.
    """Index."""

    def __init__(self, base_url: str, name: str, user: str, client_cmd_base: list[str]) -> None:
        """
        Create index.

        :param base_url: server URL up to the user segment, the index URL is built from it
        :param name: name for the index server
        :param user: the username to use
        :param client_cmd_base: the devpi client command, with its client directory, that runs index commands
        """
        self._client_cmd_base = client_cmd_base
        self._server_url = base_url
        self.name = name
        self.user = user

    def __repr__(self) -> str:
        """Return the repr of the index."""
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


def _check_call(cmd: list[str]) -> None:  # ruff:ignore[non-empty-init-module]  # Keep the helper local to the public classes.
    run(cmd, check=True, capture_output=True)  # ruff:ignore[subprocess-without-shell-equals-true] argument list


class IndexServer:  # ruff:ignore[non-empty-init-module]  # Preserve the original public module path.
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
        self._scripts = Path(scripts_dir)

        self._server_dir = self.path / "server"
        self._client_dir = self.path / "client"
        self._indexes: dict[str, Index] = {}
        self._process: Popen[str] | None = None
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
        cmd = [self._exe("devpi-init"), "--serverdir", server_at]
        cmd.extend(("--role", "standalone", "--root-passwd", self._passwd))
        if self._with_root_pypi is False:
            cmd.append("--no-root-pypi")
        _check_call(cmd)
        # 2. start the server
        cmd = [self._exe("devpi-server"), "--serverdir", server_at, "--port", str(self.port)]
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

    def _exe(self, name: str) -> str:
        return str(self._scripts / f"{name}{'.exe' if sys.platform == 'win32' else ''}")

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
        _check_call([self._exe("devpi"), "use", *base, self.url])
        _check_call([self._exe("devpi"), "login", *base, self.user, "--password", self._passwd])

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
        base = [self._exe("devpi"), "--clientdir", str(self._client_dir)]
        _check_call([*base, "index", "-c", name, *args])
        index = Index(f"{self.url}/{self.user}", name, self.user, base)
        self._indexes[name] = index
        return index


__all__ = [
    "Index",
    "IndexServer",
    "__version__",
]
