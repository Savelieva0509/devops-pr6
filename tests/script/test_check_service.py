import subprocess

import check_service


def fake_curl(returncode=0, stdout="", stderr="", calls=None):
    def run(command, **kwargs):
        if calls is not None:
            calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, returncode, stdout, stderr)
    return run


def test_reads_environment_variables(monkeypatch):
    calls = []
    monkeypatch.setenv("BASE_URL", "http://test.local:9999")
    monkeypatch.setenv("EXPECTED_RELEASE", "release-x")
    monkeypatch.setenv("CHECK_TIMEOUT", "3")
    monkeypatch.setattr(subprocess, "run",
                        fake_curl(stdout="<h1>release-x</h1>", calls=calls))

    assert check_service.main() == 0

    command, kwargs = calls[0]
    assert command[0] == "curl"
    assert command[-1] == "http://test.local:9999"
    assert kwargs["timeout"] == 3.0
    assert kwargs["capture_output"] is True
    assert kwargs["text"] is True


def test_success_message(monkeypatch, capsys):
    monkeypatch.setenv("EXPECTED_RELEASE", "release-x")
    monkeypatch.setattr(subprocess, "run", fake_curl(stdout="release-x"))

    assert check_service.main() == 0
    assert "OK" in capsys.readouterr().out


def test_wrong_release(monkeypatch, capsys):
    monkeypatch.setenv("EXPECTED_RELEASE", "release-x")
    monkeypatch.setattr(subprocess, "run", fake_curl(stdout="wrong-release"))

    assert check_service.main() == 1
    assert "немає 'release-x'" in capsys.readouterr().out


def test_curl_error(monkeypatch, capsys):
    monkeypatch.setenv("EXPECTED_RELEASE", "release-x")
    monkeypatch.setattr(subprocess, "run", fake_curl(
        returncode=7, stderr="curl: (7) Failed to connect"))

    assert check_service.main() == 1
    assert "кодом 7" in capsys.readouterr().out


def test_timeout(monkeypatch, capsys):
    def hang(command, **kwargs):
        raise subprocess.TimeoutExpired(command, kwargs["timeout"])

    monkeypatch.setenv("EXPECTED_RELEASE", "release-x")
    monkeypatch.setenv("CHECK_TIMEOUT", "2")
    monkeypatch.setattr(subprocess, "run", hang)

    assert check_service.main() == 2
    assert "ТАЙМ-АУТ" in capsys.readouterr().out


def test_missing_expected_release(monkeypatch, capsys):
    monkeypatch.delenv("EXPECTED_RELEASE", raising=False)

    assert check_service.main() == 1
    assert "EXPECTED_RELEASE" in capsys.readouterr().out
