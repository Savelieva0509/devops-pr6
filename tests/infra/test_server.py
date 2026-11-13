import json

import pytest

HTML_DIR = "/usr/share/nginx/html"


def test_nginx_configuration(host):
    result = host.run("nginx -t")
    assert result.rc == 0, result.stderr


@pytest.mark.parametrize("path", [
    "/etc/nginx/nginx.conf",
    f"{HTML_DIR}/index.html",
    f"{HTML_DIR}/health.json",
])
def test_required_file_exists(host, path):
    assert host.file(path).is_file


def test_page_contains_release(host, expected_release):
    page = host.file(f"{HTML_DIR}/index.html")
    assert page.contains(expected_release)


def test_health_file_release(host, expected_release):
    data = json.loads(host.file(f"{HTML_DIR}/health.json").content_string)
    assert data["release"] == expected_release
