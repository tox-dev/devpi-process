"""Devpi PyPI to test with."""

from __future__ import annotations

from ._index import Index
from ._server import IndexServer
from ._version import __version__

__all__ = [
    "Index",
    "IndexServer",
    "__version__",
]
