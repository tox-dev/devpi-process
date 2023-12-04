from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from httpx import get

from devpi_process import IndexServer

if TYPE_CHECKING:
    from _pytest.tmpdir import TempPathFactory


def test_version() -> None:
    import devpi_process  # noqa: PLC0415

    assert devpi_process.__version__ is not None


@pytest.fixture(scope="session")
def demo_artifacts(tmp_path_factory: TempPathFactory) -> tuple[Path, Path]:
    spec = spec_from_file_location("demo_pkg_inline.build", str(Path(__file__).parent / "demo_pkg_inline" / "build.py"))
    assert spec is not None
    build = module_from_spec(spec)
    loader = spec.loader
    assert loader is not None
    loader.exec_module(build)
    base = tmp_path_factory.mktemp("wheel")
    wheel = base / build.build_wheel(str(base))
    sdist = base / build.build_sdist(str(base))
    return wheel, sdist


def test_create_server(tmp_path: Path, demo_artifacts: tuple[Path, Path]) -> None:
    with IndexServer(tmp_path) as server:
        assert repr(server)
        state = get(server.url).json()["result"]["root"]
        assert state["username"] == "root"
        assert state["indexes"] == {}

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
    with IndexServer(tmp_path, start_args=["--offline-mode"]) as server:
        assert server._process is not None  # noqa: SLF001
        assert server._process.args[-1] == "--offline-mode"  # type: ignore[index] # noqa: SLF001
