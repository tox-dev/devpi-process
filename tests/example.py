from pytest_devpi import Devpi


def test_server_parallel_requests(devpi: Devpi) -> None:
    assert devpi
