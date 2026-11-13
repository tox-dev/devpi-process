from __future__ import annotations

import socket
import sysconfig
from contextlib import ExitStack
from http import HTTPStatus
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import TYPE_CHECKING, get_type_hints

import pytest
from httpx import get

from devpi_process import Index, IndexServer, __version__

if TYPE_CHECKING:
    from types import FunctionType, ModuleType


def test_version() -> None:
    assert __version__ is not None


def test_index_upload_type_hints() -> None:
    assert get_type_hints(Index.upload)["files"] is Path


def test_public_class_module_paths() -> None:
    assert (Index.__module__, IndexServer.__module__) == ("devpi_process", "devpi_process")


@pytest.mark.parametrize(
    "method",
    [
        pytest.param(Index.use, id="index-use"),
        pytest.param(Index.upload, id="index-upload"),
        pytest.param(IndexServer.__enter__, id="server-enter"),
        pytest.param(IndexServer.create_index, id="server-create-index"),
    ],
)
def test_public_method_module_paths(method: FunctionType) -> None:
    assert method.__module__ == "devpi_process"
    assert Path(method.__code__.co_filename).name == "__init__.py"


@pytest.fixture(scope="session")
def demo_backend() -> ModuleType:
    spec = spec_from_file_location("demo_pkg_inline.build", str(Path(__file__).parent / "demo_pkg_inline" / "build.py"))
    assert spec is not None
    build = module_from_spec(spec)
    loader = spec.loader
    assert loader is not None
    loader.exec_module(build)
    return build


@pytest.fixture(scope="session")
def demo_artifacts(tmp_path_factory: pytest.TempPathFactory, demo_backend: ModuleType) -> tuple[Path, Path]:
    base = tmp_path_factory.mktemp("wheel")
    return base / demo_backend.build_wheel(str(base)), base / demo_backend.build_sdist(str(base))


def test_demo_backend_requires_no_extra_build_dependencies(demo_backend: ModuleType) -> None:
    assert demo_backend.get_requires_for_build_wheel() == []
    assert demo_backend.get_requires_for_build_sdist() == []


def test_create_server(tmp_path: Path, demo_artifacts: tuple[Path, Path]) -> None:
    with IndexServer(tmp_path) as server:
        assert repr(server)
        state = get(server.url).json()["result"]["root"]
        assert (state["username"], state["indexes"]) == ("root", {})

        server.create_index("base")

        test = server.create_index("test", f"bases={server.user}/base")
        assert repr(test)

        state = get(server.url).json()["result"]["root"]
        assert state["indexes"].keys() == {"test", "base"}

        root = get(test.url).text
        assert "demo-pkg-inline" not in root

        test.use()
        test.upload(*demo_artifacts)
        root = get(test.url).text
        assert "demo-pkg-inline" in root

        pkg = get(f"{test.url}demo-pkg-inline/").text
        assert demo_artifacts[0].name in pkg
        assert demo_artifacts[1].name in pkg


def test_create_server_with_pypi(tmp_path: Path) -> None:
    with IndexServer(tmp_path, with_root_pypi=True) as server:
        state = get(server.url).json()["result"]["root"]
        assert state["indexes"].keys() == {"pypi"}


def test_create_server_start_args(tmp_path: Path) -> None:
    with IndexServer(tmp_path, start_args=["--host", "127.0.0.1"]) as server:
        response = get(f"{server.url}/+status", headers={"Accept": "application/json"})
        assert response.status_code == HTTPStatus.OK
        assert response.json()["result"]["host"] == "127.0.0.1"


def test_server_probes_all_ipv4_interfaces(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    bound_addresses: list[socket._Address] = []

    class ProbeSocket(socket.socket):
        def bind(self, address: socket._Address) -> None:
            bound_addresses.append(address)
            super().bind(address)

    monkeypatch.setattr(socket, "socket", ProbeSocket)

    IndexServer(tmp_path)

    assert bound_addresses == [("", 0)]


def test_create_server_rejects_duplicate_index(tmp_path: Path) -> None:
    with IndexServer(tmp_path) as server:
        server.create_index("base")
        with pytest.raises(ValueError, match="index base already exists"):
            server.create_index("base")


def test_create_server_rejects_missing_scripts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sysconfig, "get_path", lambda _name: None)

    with pytest.raises(RuntimeError, match="could not get scripts folder of host interpreter"):
        IndexServer(tmp_path)


def test_create_server_reports_missing_executable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sysconfig, "get_path", lambda _name: str(tmp_path / "missing"))

    with ExitStack() as stack, pytest.raises(FileNotFoundError):
        stack.enter_context(IndexServer(tmp_path))


def test_create_server_reports_startup_failure(tmp_path: Path) -> None:
    with ExitStack() as stack, pytest.raises(RuntimeError, match="exited before it was ready"):
        stack.enter_context(IndexServer(tmp_path, start_args=["--definitely-invalid"]))
