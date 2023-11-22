# Подготовка окружения

## Зависимости

Зависимости в [fastapi-solution/requirements](fastapi-solution/requirements) разделены на базовые [base.txt](fastapi-solution/requirements/base.txt) (необходимые для работы сервиса) и дополнительные, используемые в процессе разработки.

Для установки полного набора можно использовать команду:

`pip install -r fastapi-solution/requirements/dev.txt`

## Pre-commit

Для установки автоматических проверок кода (flake8, isort) перед коммитом можно использовать команду:

`pre-commit install`

# Запуск приложения

Чтобы задать переменные окружения, можно создать файл .env по образцу [.env.example](.env.example).

Для запуска сервиса с api, Elastic Search, Redis и Nginx можно использовать команду:

`docker compose up --build`

Чтобы импортировать в Elastic тестовые данные о фильмах, жанрах и персонах с предыдущего спринта, можно использовать скрипт:

`bash import_data.sh`

После запуска должна открываться страница с документацией [http://127.0.0.1:81/api/openapi](http://127.0.0.1:81/api/openapi)

# Запуск тестов

Для запуска всех тестов можно использовать команду:

`docker compose -f fastapi-solution/tests/functional/docker-compose.yml up --build --abort-on-container-exit --exit-code-from tests`

Для запуска отдельных тестов можно указать файл или конкретный тест при помощи переменной `TESTS`, например:

`TESTS=src/test_films_search.py::test_films_search_cache docker compose -f fastapi-solution/tests/functional/docker-compose.yml up --build --abort-on-container-exit --exit-code-from tests`

# Проектная работа 5 спринта

В папке **tasks** ваша команда найдёт задачи, которые необходимо выполнить во втором спринте модуля "Сервис Async API".

Как и в прошлом спринте, мы оценили задачи в стори поинтах.

Вы можете разбить эти задачи на более маленькие, например, распределять между участниками команды не большие куски задания, а маленькие подзадачи. В таком случае не забудьте зафиксировать изменения в issues в репозитории.

**От каждого разработчика ожидается выполнение минимум 40% от общего числа стори поинтов в спринте.**
