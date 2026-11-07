from __future__ import annotations

import sys
import tarfile
from io import BytesIO
from pathlib import Path
from textwrap import dedent
from typing import Final
from zipfile import ZipFile

name = "demo_pkg_inline"
_PKG_NAME = name.replace("_", "-")

_VERSION: Final[str] = "1.0.0"
_DIST_INFO: Final[str] = f"{name}-{_VERSION}.dist-info"
_LOGIC: Final[str] = f"{name}/__init__.py"
METADATA: Final[str] = f"{_DIST_INFO}/METADATA"
wheel: Final[str] = f"{_DIST_INFO}/WHEEL"
RECORD: Final[str] = f"{_DIST_INFO}/RECORD"
_CONTENT = {
    _LOGIC: f"def do():\n    print('greetings from {name}')",
    METADATA: f"""
        Metadata-Version: 2.1
        Name: {_PKG_NAME}
        Version: {_VERSION}
        Summary: UNKNOWN
        Home-page: UNKNOWN
        Author: UNKNOWN
        Author-email: UNKNOWN
        License: UNKNOWN
        Platform: UNKNOWN

        UNKNOWN
       """,
    wheel: f"""
        Wheel-Version: 1.0
        Generator: {name}-{_VERSION}
        Root-Is-Purelib: true
        Tag: py{sys.version_info[0]}-none-any
       """,
    f"{_DIST_INFO}/top_level.txt": name,
    RECORD: f"""
        {name}/__init__.py,,
        {_DIST_INFO}/METADATA,,
        {_DIST_INFO}/WHEEL,,
        {_DIST_INFO}/top_level.txt,,
        {_DIST_INFO}/RECORD,,
       """,
}


def build_wheel(
    wheel_directory: str,
    metadata_directory: str | None = None,  # ruff:ignore[unused-function-argument]
    config_settings: None = None,  # ruff:ignore[unused-function-argument]
) -> str:
    base_name = f"{name}-{_VERSION}-py{sys.version_info[0]}-none-any.whl"
    with ZipFile(str(Path(wheel_directory) / base_name), "w") as zip_file_handler:
        for arc_name, data in _CONTENT.items():  # pragma: no branch
            zip_file_handler.writestr(arc_name, dedent(data).strip())
    return base_name


def get_requires_for_build_wheel(
    config_settings: None = None,  # ruff:ignore[unused-function-argument]
) -> list[str]:
    return []  # pragma: no cover # only executed in non-host pythons


def build_sdist(
    sdist_directory: str,
    config_settings: None = None,  # ruff:ignore[unused-function-argument]
) -> str:
    result = f"{name}-{_VERSION}.tar.gz"
    with tarfile.open(str(Path(sdist_directory) / result), "w:gz") as tar:
        root = Path(__file__).parent
        tar.add(str(root / "build.py"), "build.py")
        tar.add(str(root / "pyproject.toml"), "pyproject.toml")

        pkg_info = dedent(_CONTENT[METADATA]).strip().encode("utf-8")
        info = tarfile.TarInfo("PKG-INFO")
        info.size = len(pkg_info)
        tar.addfile(info, BytesIO(pkg_info))

    return result


def get_requires_for_build_sdist(
    config_settings: None = None,  # ruff:ignore[unused-function-argument]
) -> list[str]:
    return []  # pragma: no cover # only executed in non-host pythons
