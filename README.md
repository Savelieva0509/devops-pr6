# Практична робота 6 — автоматизована перевірка контейнеризованого сервісу

Бабенко Людмила. Ідентифікатор роботи: `devops6-babenko`.

Статичний вебсервіс на nginx у Docker і набір автоматичних перевірок, які запускаються
локально та в GitHub Actions.

## Що є в сервісі

| Адреса | Відповідь |
|---|---|
| `/` | 200, сторінка з ідентифікатором `devops6-babenko` |
| `/health.json` | 200, `{"status": "ok", "release": "devops6-babenko"}` |
| `/missing-page` | 404 |

Базовий образ закріплено версією і digest:
`nginx:1.31.8-alpine@sha256:713fc2ebfd92e8217db451477182ee91944b123d2b1ee9fd5a8c6e91ca6c3a11`.
Версії Python-залежностей зафіксовано в `requirements.txt`.

## Структура

    Dockerfile, index.html, health.json   сервіс
    check_service.py                      команда перевірки (curl через subprocess)
    pytest.ini                            налаштування pytest
    tests/conftest.py                     спільні фікстури (BASE_URL, EXPECTED_RELEASE, http_get)
    tests/infra/test_server.py            перевірки всередині контейнера (Testinfra)
    tests/http/test_http.py               HTTP-перевірки ззовні
    tests/script/test_check_service.py    ізольовані тести скрипту (monkeypatch, capsys)
    .github/workflows/ci.yml              перевірки в GitHub Actions
    EXPERIMENTS.md                        три експерименти зі збоями

## Запуск локально (Linux / WSL, Docker у режимі Linux-контейнерів)

    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install -r requirements.txt

    docker build -t devops6-babenko .
    docker run -d --name devops6-web -p 127.0.0.1:8080:80 devops6-babenko

    export BASE_URL=http://127.0.0.1:8080
    export EXPECTED_RELEASE=devops6-babenko
    export CHECK_TIMEOUT=5

    python -m pytest -v --hosts=docker://devops6-web     # усі 17 тестів
    python check_service.py; echo "Код завершення: $?"

    docker rm -f devops6-web                             # прибрати після перевірки

Окремі групи: `python -m pytest -v --hosts=docker://devops6-web tests/infra`,
`python -m pytest -v tests/http`, `python -m pytest -v tests/script`.

## Змінні середовища

| Змінна | Призначення |
|---|---|
| `BASE_URL` | адреса сервісу для HTTP-тестів і скрипту |
| `EXPECTED_RELEASE` | очікуваний ідентифікатор (задається окремо від файлів сервісу) |
| `CHECK_TIMEOUT` | тайм-аут HTTP-запитів і curl, с (типово 5) |

## Команда перевірки `check_service.py`

Запускає `curl` через `subprocess.run` (команда списком, `capture_output=True`, `text=True`,
`timeout=CHECK_TIMEOUT`) і перевіряє код curl та наявність ідентифікатора у відповіді.
Коди завершення: **0** — успіх, **1** — перевірка не пройшла, **2** — тайм-аут
(`subprocess.TimeoutExpired`).

## Навіщо окремо перевірки всередині контейнера і ззовні

- **Всередині (Testinfra через `docker exec`)** перевіряють, *як сервіс зібрано і налаштовано*:
  `nginx -t`, наявність файлів, вміст файлів. Вони не залежать від мережі, тому точно показують
  проблему конфігурації або вмісту, але не бачать, чи до сервісу можна дістатися.
- **Ззовні (HTTP з машини, де запущено pytest)** перевіряють те, що отримує користувач: доступність,
  HTTP-коди, вміст відповіді, коректність JSON. Вони не бачать, *чому* щось не так.

Експеримент 2 (помилковий порт) це показує: усі перевірки всередині контейнера пройшли, а всі
HTTP-перевірки впали. Експеримент 1 (неправильна версія): сервер відповідав 200, і лише перевірки
вмісту виявили проблему. Деталі — у `EXPERIMENTS.md`.

## GitHub Actions

Workflow `.github/workflows/ci.yml` на `ubuntu-latest`: отримує файли, ставить Python 3.14 і
залежності, збирає образ, запускає контейнер, чекає на відповідь сервісу (не довше 30 с), запускає
всі тести і `check_service.py`, виконує етап «Готовність підтверджено» лише після успіху всіх
перевірок, завжди зберігає звіт pytest (JUnit XML) і журнал контейнера як артефакт `test-reports`
і видаляє тестовий контейнер.
