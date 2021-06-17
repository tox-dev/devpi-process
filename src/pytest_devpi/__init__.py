from types import TracebackType
from typing import Iterator, Optional, Type

import pytest

from .version import __version__


class Devpi:
    def __enter__(self) -> "Devpi":
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],  # noqa: U100
        exc_val: Optional[BaseException],  # noqa: U100
        exc_tb: Optional[TracebackType],  # noqa: U100
    ) -> None:
        """ok"""


@pytest.fixture()
def devpi() -> Iterator[Devpi]:
    with Devpi() as devpi:
        yield devpi


__all__ = [
    "__version__",
]
