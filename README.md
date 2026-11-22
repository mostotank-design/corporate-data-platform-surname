# Corporate Data Platform

Учебный проект по дисциплине «Современные технологии разработки программного обеспечения».

## Назначение

Платформа предназначена для получения, хранения, обработки и аналитики корпоративных данных.

## Компоненты

- Веб-приложение — работа с организациями, порт 8000.
- PostgreSQL — операционные данные.
- Apache Airflow — ETL-конвейер, интерфейс на порту 8081.
- RustFS — объектное хранилище с S3 API на порту 9000 и веб-консолью на порту 9001.
- DuckDB — аналитические SQL-запросы к CSV и объектам Data Lake.
- Kubernetes — манифесты развертывания находятся в каталоге kubernetes/.

## Запуск Docker Compose

Создайте локальный .env из примера и укажите ключи RustFS:

    Copy-Item .env.example .env
    docker compose up -d --build
    docker compose ps

Сервисы доступны локально:

- Приложение: http://localhost:8000
- Airflow: http://localhost:8081
- RustFS S3 API: http://localhost:9000
- RustFS Console: http://localhost:9001

Не добавляйте .env с ключами доступа в Git.

## DuckDB: аналитика данных

Установите зависимости из корня проекта:

    python -m pip install -r analytics/requirements.txt

Запустите исследование и аналитические запросы к RAW CSV:

    python analytics/explore_data.py
    python analytics/analyze_companies.py

Скрипт analyze_companies.py рассчитывает сводные показатели, группировки по городам и отраслям, применяет HAVING и формирует:

- analytics/reports/city_analytics.csv
- analytics/reports/conclusions.md

Для прямого чтения объектов из RustFS через DuckDB:

    python analytics/analyze_rustfs.py

Скрипт использует расширение DuckDB httpfs. Если оно не устанавливается, загрузите объекты через boto3 и проанализируйте локальные копии:

    python analytics/download_rustfs.py

Подробнее: docs/data-lake.md и docs/analytics.md.

## Kubernetes

Манифесты находятся в каталоге kubernetes/. Для локального кластера Docker Desktop:

    kubectl apply -f kubernetes/deployment.yaml
    kubectl get pods

## Автор

Первушин Егор, группа ЭУ 212.


## NetworkX: графовая аналитика

Графовый модуль строит модель организаций, городов и отраслей из
`data/raw/companies.csv`. Вершины имеют типы `company`, `city` и `industry`,
а ребра отражают расположение организации в городе и принадлежность к отрасли.
Модуль анализирует соседей, общие связи, степени вершин, центральность,
компоненты связности и кратчайшие пути.

Установка зависимостей:

    python -m pip install -r analytics/requirements.txt

Запуск примера и анализа:

    python analytics/graphs/first_graph.py
    python analytics/graphs/build_company_graph.py
    python analytics/graphs/visualize_graph.py

Визуализация сохраняется в `analytics/reports/company_graph.png`, результаты
анализа описаны в `analytics/reports/graph_analysis.md`. Подробности модели:
`docs/graph-model.md`.
