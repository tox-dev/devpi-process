from __future__ import annotations

import sys
import tarfile
from io import BytesIO
from pathlib import Path
from textwrap import dedent
from zipfile import ZipFile

name = "demo_pkg_inline"
pkg_name = name.replace("_", "-")

version = "1.0.0"
dist_info = f"{name}-{version}.dist-info"
logic = f"{name}/__init__.py"
metadata = f"{dist_info}/METADATA"
wheel = f"{dist_info}/WHEEL"
record = f"{dist_info}/RECORD"
content = {
    logic: f"def do():\n    print('greetings from {name}')",
    metadata: f"""
        Metadata-Version: 2.1
        Name: {pkg_name}
        Version: {version}
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
        Generator: {name}-{version}
        Root-Is-Purelib: true
        Tag: py{sys.version_info[0]}-none-any
       """,
    f"{dist_info}/top_level.txt": name,
    record: f"""
        {name}/__init__.py,,
        {dist_info}/METADATA,,
        {dist_info}/WHEEL,,
        {dist_info}/top_level.txt,,
        {dist_info}/RECORD,,
       """,
}


def build_wheel(
    wheel_directory: str,
    metadata_directory: str | None = None,  # noqa: ARG001
    config_settings: None = None,  # noqa: ARG001
) -> str:
    base_name = f"{name}-{version}-py{sys.version_info[0]}-none-any.whl"
    path = Path(wheel_directory) / base_name
    with ZipFile(str(path), "w") as zip_file_handler:
        for arc_name, data in content.items():  # pragma: no branch
            zip_file_handler.writestr(arc_name, dedent(data).strip())
    return base_name


def get_requires_for_build_wheel(
    config_settings: None = None,  # noqa: ARG001
) -> list[str]:
    return []  # pragma: no cover # only executed in non-host pythons


def build_sdist(
    sdist_directory: str,
    config_settings: None = None,  # noqa: ARG001
) -> str:
    result = f"{name}-{version}.tar.gz"
    with tarfile.open(str(Path(sdist_directory) / result), "w:gz") as tar:
        root = Path(__file__).parent
        tar.add(str(root / "build.py"), "build.py")
        tar.add(str(root / "pyproject.toml"), "pyproject.toml")

        pkg_info = dedent(content[metadata]).strip().encode("utf-8")
        info = tarfile.TarInfo("PKG-INFO")
        info.size = len(pkg_info)
        tar.addfile(info, BytesIO(pkg_info))

    return result


def get_requires_for_build_sdist(
    config_settings: None = None,  # noqa: ARG001
) -> list[str]:
    return []  # pragma: no cover # only executed in non-host pythons
