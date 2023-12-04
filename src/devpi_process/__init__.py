"""Devpi PyPI to test with."""

from __future__ import annotations

import random
import socket
import string
import sys
import sysconfig
from contextlib import closing
from pathlib import Path
from subprocess import PIPE, Popen, run  # noqa: S404
from threading import Thread
from typing import IO, TYPE_CHECKING, Iterator, Sequence, cast

from ._version import __version__

if TYPE_CHECKING:
    from types import TracebackType

    if sys.version_info >= (3, 11):  # pragma: no cover (py311+)
        from typing import Self
    else:  # pragma: no cover (<py311)
        from typing_extensions import Self


def _check_call(cmd: list[str]) -> None:
    run(cmd, check=True, capture_output=True)  # noqa: S603


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

    @property
    def url(self) -> str:
        """:return: the URL to the index server"""
        return f"{self._server_url}/{self.name}/+simple/"

    def use(self) -> None:
        """Use this index server."""
        _check_call([*self._client_cmd_base, "use", f"{self.user}/{self.name}"])

    def upload(self, *files: Path) -> None:
        """
        Upload packages to the index.

        :param files: the files to upload
        """
        cmd = self._client_cmd_base + ["upload", "--index", self.name] + [str(i) for i in files]
        _check_call(cmd)

    def __repr__(self) -> str:
        """:return: repr of the index"""
        return f"{self.__class__.__name__}(url={self.url})"


class IndexServer:
    """A PyPI index server locally."""

    def __init__(
        self,
        path: Path,
        with_root_pypi: bool = False,  # noqa: FBT001, FBT002
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

        self.host, self.port = "localhost", _find_free_port()
        self._passwd = "".join(random.choices(string.ascii_letters, k=8))  # noqa: S311

        scripts_dir = sysconfig.get_path("scripts")
        if scripts_dir is None:
            msg = "could not get scripts folder of host interpreter"  # pragma: no cover
            raise RuntimeError(msg)  # pragma: no cover

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

    @property
    def user(self) -> str:
        """:return: username of the index server"""
        return "root"

    def __enter__(self) -> Self:
        """:return: start the index server"""
        self._create_and_start_server()
        self._setup_client()
        return self

    def _create_and_start_server(self) -> None:
        self._server_dir.mkdir(exist_ok=True)
        server_at = str(self._server_dir)
        # 1. create the server
        cmd = [self._init, "--serverdir", server_at]
        cmd.extend(("--role", "standalone", "--root-passwd", self._passwd))
        if self._with_root_pypi is False:
            cmd.append("--no-root-pypi")
        _check_call(cmd)
        # 2. start the server
        cmd = [self._server, "--serverdir", server_at, "--port", str(self.port)]
        cmd.extend(self._start_args)
        self._process = Popen(cmd, stdout=PIPE, universal_newlines=True)  # noqa: S603
        stdout = self._drain_stdout()
        for line in stdout:  # pragma: no branch # will always loop at least once
            if "serving at url" in line:

                def _keep_draining() -> None:
                    for _ in stdout:
                        pass

                # important to keep draining the stdout, otherwise once the buffer is full Windows blocks the process
                self._stdout_drain = Thread(target=_keep_draining, name="tox-test-stdout-drain")
                self._stdout_drain.start()
                break

    def _drain_stdout(self) -> Iterator[str]:
        process = cast("Popen[str]", self._process)
        stdout = cast(IO[str], process.stdout)
        while True:
            if process.poll() is not None:  # pragma: no cover
                print(f"devpi server with pid {process.pid} at {self._server_dir} died")  # noqa: T201
                break
            yield stdout.readline()

    def _setup_client(self) -> None:
        """Create a user on the server and authenticate it."""
        self._client_dir.mkdir(exist_ok=True)
        base = ["--clientdir", str(self._client_dir)]
        _check_call([self._client, "use", *base, self.url])
        _check_call([self._client, "login", *base, self.user, "--password", self._passwd])

    def create_index(self, name: str, *args: str) -> Index:
        """
        Create an index on the server.

        :param name: with name
        :param args: additional arguments
        :return: the created index
        """
        if name in self._indexes:  # pragma: no cover
            msg = f"index {name} already exists"
            raise ValueError(msg)
        base = [self._client, "--clientdir", str(self._client_dir)]
        _check_call([*base, "index", "-c", name, *args])
        index = Index(f"{self.url}/{self.user}", name, self.user, base)
        self._indexes[name] = index
        return index

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """
        Stop the index server.

        :param exc_type:
        :param exc_val:
        :param exc_tb:
        """
        if self._process is not None:  # pragma: no cover # defend against devpi startup fail
            self._process.terminate()
        if self._stdout_drain is not None and self._stdout_drain.is_alive():  # pragma: no cover # devpi startup fail
            self._stdout_drain.join()

    @property
    def url(self) -> str:
        """:return: url to the index server"""
        return f"http://{self.host}:{self.port}"

    def __repr__(self) -> str:
        """:return: repr of the index server"""
        return f"{self.__class__.__name__}(url={self.url}, indexes={list(self._indexes)})"


def _find_free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as socket_handler:
        socket_handler.bind(("", 0))
        return cast(int, socket_handler.getsockname()[1])


__all__ = [
    "Index",
    "IndexServer",
    "__version__",
]
