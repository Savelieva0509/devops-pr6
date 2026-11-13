import os

import pytest
import requests


def _required_env(name):
    value = os.environ.get(name)
    if not value:
        pytest.fail(f"Не задано змінну середовища {name}")
    return value


@pytest.fixture(scope="session")
def expected_release():
    return _required_env("EXPECTED_RELEASE")


@pytest.fixture(scope="session")
def base_url():
    return _required_env("BASE_URL").rstrip("/")


@pytest.fixture(scope="session")
def http_timeout():
    return float(os.environ.get("CHECK_TIMEOUT", "5"))


@pytest.fixture(scope="session")
def http_get(base_url, http_timeout):
    session = requests.Session()

    def get(path):
        return session.get(base_url + path, timeout=http_timeout)

    yield get
    session.close()
