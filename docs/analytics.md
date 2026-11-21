# Аналитический модуль Corporate Data Platform

## Назначение

Аналитическая обработка корпоративных данных с помощью DuckDB. DuckDB читает CSV и выполняет SQL-запросы без отдельного сервера базы данных.

## Источники данных

- PostgreSQL — операционные записи организаций.
- RustFS — S3-совместимое объектное хранилище.
- RAW: `corporate-raw/companies/companies.csv`.
- PROCESSED: `corporate-processed/reports/companies_by_city.csv`.

## Установка и запуск

Из корня проекта:

```powershell
python -m pip install -r analytics/requirements.txt
python analytics/explore_data.py
python analytics/analyze_companies.py
python analytics/analyze_rustfs.py
```

Для прямого чтения объектов RustFS используется DuckDB extension `httpfs`. При первом запуске DuckDB скачивает расширение, поэтому требуется доступ к его репозиторию.

Если `httpfs` установить не удается, скачайте объекты через boto3 и анализируйте локальные копии:

```powershell
python analytics/download_rustfs.py
```

Ключи RustFS берутся из локального файла `.env` и не сохраняются в исходном коде.

## Основные операции

- Чтение CSV с помощью `read_csv_auto()`.
- Фильтрация через `WHERE`, сортировка через `ORDER BY`.
- Группировка через `GROUP BY` и фильтрация групп через `HAVING`.
- Подсчет количества, суммы, среднего, максимума и минимума.
- Сравнение исходных RAW-данных и агрегированного PROCESSED-набора.

## Результаты

После запуска `analyze_companies.py` создаются:

- `analytics/reports/city_analytics.csv` — агрегаты по городам.
- `analytics/reports/conclusions.md` — выводы по фактическим данным и ограничения анализа.

## Архитектура

```text
PostgreSQL → Apache Airflow → RustFS Data Lake → DuckDB → Аналитический отчет
```

PostgreSQL остается источником операционных записей, Airflow формирует обработанный набор, RustFS хранит объекты, а DuckDB выполняет аналитические запросы к CSV.
