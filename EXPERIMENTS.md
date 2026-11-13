# Експерименти зі збоями

Кожен експеримент починався зі справного середовища (17 passed, `check_service.py` -> код 0).
Прогноз записувався до внесення несправності.

Змінні середовища: `BASE_URL=http://127.0.0.1:8080`, `EXPECTED_RELEASE=devops6-babenko`.

## Експеримент 1. Неправильна версія

**Несправність:** у запущеному контейнері на сторінці замінено ідентифікатор, сервер не зупиняли:

    docker exec devops6-web sed -i 's/devops6-babenko/devops6-wrong/g' /usr/share/nginx/html/index.html

**Прогноз:** `nginx -t`, 3 перевірки файлів, `health.json` (infra і HTTP), коди 200/200/404 і тести
скрипту пройдуть; впадуть 2 перевірки вмісту сторінки (`test_page_contains_release`,
`test_index_contains_release`); `check_service.py` -> код 1. Разом: 15 passed, 2 failed.

**Фактичний результат:** збігся з прогнозом.

    HTTP-код /: 200
    FAILED tests/http/test_http.py::test_index_contains_release
    FAILED tests/infra/test_server.py::test_page_contains_release[docker://devops6-web]
    2 failed, 15 passed in 2.91s
    ПОМИЛКА: у відповіді http://127.0.0.1:8080 немає 'devops6-babenko'
    Код завершення: 1

**Причина:** сервер працює і відповідає 200, але віддає не ту версію сторінки.
Перевірки HTTP-кодів цього не бачать — проблему виявляють лише перевірки вмісту
(всередині контейнера і ззовні) та `check_service.py`.

**Відновлення:** контейнер перестворено з образу, зібраного з файлів репозиторію:

    docker rm -f devops6-web
    docker run -d --name devops6-web -p 127.0.0.1:8080:80 devops6-babenko

Повторна перевірка: 17 passed in 2.59s, `check_service.py` -> OK, код 0.

## Експеримент 2. Помилковий порт

**Несправність:** контейнер опубліковано на порту 8081, `BASE_URL` залишився `http://127.0.0.1:8080`:

    docker rm -f devops6-web
    docker run -d --name devops6-web -p 127.0.0.1:8081:80 devops6-babenko

**Прогноз:** усі 6 перевірок infra пройдуть (Testinfra працює через `docker exec`, мережевий порт
для неї не має значення); усі 5 HTTP-перевірок впадуть з помилкою з'єднання; тести скрипту пройдуть;
`check_service.py` -> код 1 (curl не з'єднається, тайм-ауту немає). Разом: 5 failed, 12 passed.

**Фактичний результат:** збігся з прогнозом.

    devops6-web  127.0.0.1:8081->80/tcp
    BASE_URL=http://127.0.0.1:8080
    FAILED tests/http/test_http.py::test_status_code[/-200] - requests.exceptions.ConnectionError: ... port=8080
    ... (так само всі 5 HTTP-тестів)
    5 failed, 12 passed in 2.91s
    ПОМИЛКА: curl завершився з кодом 7: curl: (7) Failed to connect to 127.0.0.1 port 8080 after 0 ms
    Код завершення: 1

**Причина:** сервіс справний, але опублікований не на тій адресі, на яку звертаються клієнти.
Перевірки всередині контейнера проходять, бо потрапляють у контейнер через `docker exec` в обхід
мережі й опублікованих портів. Недоступність для користувачів бачать лише зовнішні HTTP-перевірки.

**Відновлення:** контейнер знову запущено на порту 8080 (як у README):

    docker rm -f devops6-web
    docker run -d --name devops6-web -p 127.0.0.1:8080:80 devops6-babenko

Повторна перевірка: 17 passed in 2.25s, `check_service.py` -> OK, код 0.

## Експеримент 3. Зависання сервісу

**Несправність:** процеси контейнера призупинено:

    docker pause devops6-web

**Прогноз:** `check_service.py` з'єднається, але відповіді не дочекається: через `CHECK_TIMEOUT=3` с
спрацює `subprocess.TimeoutExpired`, скрипт надрукує «ТАЙМ-АУТ» і завершиться з кодом 2;
5 HTTP-тестів впадуть з `ReadTimeout`; 6 тестів infra впадуть, бо Docker не виконує `docker exec`
у призупиненому контейнері; тести скрипту пройдуть. Разом: 11 failed, 6 passed.

**Фактичний результат:** збігся з прогнозом.

    devops6-web  Up About a minute (Paused)
    ТАЙМ-АУТ: http://127.0.0.1:8080 не відповів за 3 с
    Код завершення: 2
    real    0m3.081s
    FAILED tests/http/test_http.py::test_status_code[/-200] - requests.exceptions.ReadTimeout ...
    FAILED tests/infra/test_server.py::test_nginx_configuration[docker://devops6-web] - AssertionError:
      Error response from daemon: Container devops6-web is paused, unpause the c...
    11 failed, 6 passed in 16.27s

**Причина:** процеси nginx заморожені: з'єднання приймається, але відповідь не надходить.
Скрипт не зависає разом із сервісом, а завершується рівно за `CHECK_TIMEOUT` (3,08 с) з окремим
кодом 2 і повідомленням «ТАЙМ-АУТ» — тобто правильно називає причину (не «не та версія» і не
«немає з'єднання»).

**Відновлення:**

    docker unpause devops6-web

Повторна перевірка: 17 passed, `check_service.py` -> OK, код 0.
