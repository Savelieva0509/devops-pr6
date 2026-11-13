import pytest


@pytest.mark.parametrize("path, expected_status", [
    ("/", 200),
    ("/health.json", 200),
    ("/missing-page", 404),
])
def test_status_code(http_get, path, expected_status):
    response = http_get(path)
    assert response.status_code == expected_status


def test_index_contains_release(http_get, expected_release):
    response = http_get("/")
    assert response.status_code == 200
    assert expected_release in response.text


def test_health_json(http_get, expected_release):
    response = http_get("/health.json")
    assert response.status_code == 200
    assert "application/json" in response.headers["Content-Type"]
    data = response.json()
    assert data["status"] == "ok"
    assert data["release"] == expected_release
