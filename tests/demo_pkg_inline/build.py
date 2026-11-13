from __future__ import annotations

import sys
import tarfile
from io import BytesIO
from pathlib import Path
from textwrap import dedent
from types import MappingProxyType
from typing import Final
from zipfile import ZipFile

_NAME: Final[str] = "demo_pkg_inline"
_PKG_NAME: Final[str] = _NAME.replace("_", "-")

_VERSION: Final[str] = "1.0.0"
_DIST_INFO: Final[str] = f"{_NAME}-{_VERSION}.dist-info"
_LOGIC: Final[str] = f"{_NAME}/__init__.py"
_METADATA: Final[str] = f"{_DIST_INFO}/METADATA"
_WHEEL: Final[str] = f"{_DIST_INFO}/WHEEL"
_RECORD: Final[str] = f"{_DIST_INFO}/RECORD"
_CONTENT: Final[MappingProxyType[str, str]] = MappingProxyType({
    _LOGIC: f"def do():\n    print('greetings from {_NAME}')",
    _METADATA: f"""
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
    _WHEEL: f"""
        Wheel-Version: 1.0
        Generator: {_NAME}-{_VERSION}
        Root-Is-Purelib: true
        Tag: py{sys.version_info[0]}-none-any
       """,
    f"{_DIST_INFO}/top_level.txt": _NAME,
    _RECORD: f"""
        {_NAME}/__init__.py,,
        {_DIST_INFO}/METADATA,,
        {_DIST_INFO}/WHEEL,,
        {_DIST_INFO}/top_level.txt,,
        {_DIST_INFO}/RECORD,,
       """,
})


def build_wheel(
    wheel_directory: str,
    metadata_directory: str | None = None,  # ruff:ignore[unused-function-argument]  # PEP 517 signature
    config_settings: None = None,  # ruff:ignore[unused-function-argument]  # PEP 517 signature
) -> str:
    base_name = f"{_NAME}-{_VERSION}-py{sys.version_info[0]}-none-any.whl"
    with ZipFile(str(Path(wheel_directory) / base_name), "w") as zip_file_handler:
        for arc_name, data in _CONTENT.items():  # pragma: no branch  # _CONTENT is nonempty
            zip_file_handler.writestr(arc_name, dedent(data).strip())
    return base_name


# PEP 517 requires the unused argument.
def get_requires_for_build_wheel(config_settings: None = None) -> list[str]:  # ruff:ignore[unused-function-argument]
    return []


def build_sdist(
    sdist_directory: str,
    config_settings: None = None,  # ruff:ignore[unused-function-argument]  # PEP 517 signature
) -> str:
    result = f"{_NAME}-{_VERSION}.tar.gz"
    with tarfile.open(str(Path(sdist_directory) / result), "w:gz") as tar:
        root = Path(__file__).parent
        tar.add(str(root / "build.py"), "build.py")
        tar.add(str(root / "pyproject.toml"), "pyproject.toml")

        pkg_info = dedent(_CONTENT[_METADATA]).strip().encode("utf-8")
        info = tarfile.TarInfo("PKG-INFO")
        info.size = len(pkg_info)
        tar.addfile(info, BytesIO(pkg_info))

    return result


# PEP 517 requires the unused argument.
def get_requires_for_build_sdist(config_settings: None = None) -> list[str]:  # ruff:ignore[unused-function-argument]
    return []
