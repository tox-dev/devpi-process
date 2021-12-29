# devpi-process

[![PyPI](https://img.shields.io/pypi/v/devpi-process?style=flat-square)](https://pypi.org/project/devpi-process)
[![PyPI - Implementation](https://img.shields.io/pypi/implementation/devpi-process?style=flat-square)](https://pypi.org/project/devpi-process)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/devpi-process?style=flat-square)](https://pypi.org/project/devpi-process)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/devpi-process?style=flat-square)](https://pypistats.org/packages/devpi-process)
[![PyPI - License](https://img.shields.io/pypi/l/devpi-process?style=flat-square)](https://opensource.org/licenses/MIT)
[![check](https://github.com/tox-dev/devpi-process/workflows/check/badge.svg)](https://github.com/tox-dev/devpi-process/actions?query=workflow%3Acheck)
[![Code style:
black](https://img.shields.io/badge/code%20style-black-000000.svg?style=flat-square)](https://github.com/psf/black)

Allows you to create [devpi](https://devpi.net/docs/devpi/devpi/stable/+d/index.html) server process with indexes, and
upload artifacts to that programmatically.

## install

```sh
pip install devpi-process
```

## use

```python
from pathlib import Path

from devpi_process import Index, IndexServer

with IndexServer(Path("server-dir")) as server:
    # create an index mirroring an Artifactory instance
    magic_index_url = "https://magic.com/artifactory/api/pypi/magic-pypi/simple"
    base_name = "magic"
    server.create_index(base_name, "type=mirror", f"mirror_url={magic_index_url}")

    # create a dev index server that bases of magic PyPI, and upload a wheel to it
    dev: Index = server.create_index("dev", f"bases={server.user}/{base_name}")
    dev.upload("magic-2.24.0-py3-none-any.whl")

    assert dev.url  # point the tool consuming the index server to this
```
