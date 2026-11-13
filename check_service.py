"""Перевірка сервісу через curl.

Змінні середовища:
  BASE_URL          адреса сервісу (типово http://127.0.0.1:8080)
  EXPECTED_RELEASE  ідентифікатор, який має бути у відповіді
  CHECK_TIMEOUT     скільки секунд чекати (типово 5)

Коди завершення: 0 - успіх, 1 - перевірка не пройшла, 2 - тайм-аут.
"""
import os
import subprocess
import sys


def main():
    base_url = os.environ.get("BASE_URL", "http://127.0.0.1:8080")
    expected = os.environ.get("EXPECTED_RELEASE", "")
    timeout = float(os.environ.get("CHECK_TIMEOUT", "5"))

    if not expected:
        print("ПОМИЛКА: не задано EXPECTED_RELEASE")
        return 1

    command = ["curl", "--silent", "--show-error", "--fail", base_url]
    try:
        result = subprocess.run(command, capture_output=True, text=True,
                                timeout=timeout)
    except subprocess.TimeoutExpired:
        print(f"ТАЙМ-АУТ: {base_url} не відповів за {timeout:g} с")
        return 2

    if result.returncode != 0:
        print(f"ПОМИЛКА: curl завершився з кодом {result.returncode}: "
              f"{result.stderr.strip()}")
        return 1
    if expected not in result.stdout:
        print(f"ПОМИЛКА: у відповіді {base_url} немає '{expected}'")
        return 1

    print(f"OK: {base_url} відповідає, знайдено '{expected}'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
