from pathlib import Path
from shutil import copy2

import pytest
from _pytest.monkeypatch import MonkeyPatch
from _pytest.pytester import Testdir

_EXAMPLE = Path(__file__).parent / "example.py"


def test_version() -> None:
    import pytest_devpi

    assert pytest_devpi.__version__ is not None


@pytest.fixture()
def example(testdir: Testdir) -> Testdir:
    dest = Path(str(testdir.tmpdir / "test_example.py"))
    # dest.symlink_to(_EXAMPLE)  # for local debugging use this
    copy2(str(_EXAMPLE), str(dest))
    return testdir


def test_progress_no_v(example: Testdir) -> None:
    result = example.runpytest()
    result.assert_outcomes(passed=1)
