from __future__ import annotations

import os
import sys
import tarfile
from io import BytesIO
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
    metadata: """
        Metadata-Version: 2.1
        Name: {}
        Version: {}
        Summary: UNKNOWN
        Home-page: UNKNOWN
        Author: UNKNOWN
        Author-email: UNKNOWN
        License: UNKNOWN
        Platform: UNKNOWN

        UNKNOWN
       """.format(
        pkg_name, version
    ),
    wheel: """
        Wheel-Version: 1.0
        Generator: {}-{}
        Root-Is-Purelib: true
        Tag: py{}-none-any
       """.format(
        name, version, sys.version_info[0]
    ),
    f"{dist_info}/top_level.txt": name,
    record: """
        {0}/__init__.py,,
        {1}/METADATA,,
        {1}/WHEEL,,
        {1}/top_level.txt,,
        {1}/RECORD,,
       """.format(
        name, dist_info
    ),
}


def build_wheel(
    wheel_directory: str,
    metadata_directory: str | None = None,  # noqa: U100
    config_settings: None = None,  # noqa: U100
) -> str:
    base_name = f"{name}-{version}-py{sys.version_info[0]}-none-any.whl"
    path = os.path.join(wheel_directory, base_name)
    with ZipFile(path, "w") as zip_file_handler:
        for arc_name, data in content.items():  # pragma: no branch
            zip_file_handler.writestr(arc_name, dedent(data).strip())
    return base_name


def get_requires_for_build_wheel(
    config_settings: None = None,  # noqa: U100
) -> list[str]:
    return []  # pragma: no cover # only executed in non-host pythons


def build_sdist(
    sdist_directory: str,
    config_settings: None = None,  # noqa: U100
) -> str:
    result = f"{name}-{version}.tar.gz"
    with tarfile.open(os.path.join(sdist_directory, result), "w:gz") as tar:
        root = os.path.dirname(os.path.abspath(__file__))
        tar.add(os.path.join(root, "build.py"), "build.py")
        tar.add(os.path.join(root, "pyproject.toml"), "pyproject.toml")

        pkg_info = dedent(content[metadata]).strip().encode("utf-8")
        info = tarfile.TarInfo("PKG-INFO")
        info.size = len(pkg_info)
        tar.addfile(info, BytesIO(pkg_info))

    return result


def get_requires_for_build_sdist(
    config_settings: None = None,  # noqa: U100
) -> list[str]:
    return []  # pragma: no cover # only executed in non-host pythons
