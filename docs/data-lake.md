# Data Lake Corporate Data Platform

## Объектное хранилище

В проекте используется RustFS — объектное хранилище с S3-совместимым API.

- S3 API: `http://localhost:9000`
- Web Console: `http://localhost:9001`

Перед запуском скопируйте `.env.example` в `.env` и задайте локальные ключи RustFS. Файл `.env` игнорируется Git. Для учебной работы можно использовать ключи из методички; не публикуйте их и не открывайте порты в Интернет. Порты API и консоли привязаны к localhost.

## Структура Data Lake

| Зона | Bucket | Object key | Содержимое |
| --- | --- | --- | --- |
| RAW | `corporate-raw` | `companies/companies.csv` | Исходные записи из PostgreSQL |
| PROCESSED | `corporate-processed` | `reports/companies_by_city.csv` | Агрегат по городам, сформированный Airflow |

RAW и PROCESSED вынесены в отдельные бакеты, чтобы не смешивать исходный набор с результатом преобразования.

## RAW

Источник — PostgreSQL, таблица `companies`. В репозитории находится экспорт исходных пяти записей из `database/init.sql` в `data/raw/companies.csv`. Если в вашей существующей базе уже есть дополнительные записи, обновите CSV по фактическому содержимому таблицы перед загрузкой.

## PROCESSED

DAG `corporate_etl` сохраняет CSV локально в `airflow/output/companies_by_city.csv`, после чего задача `upload_to_rustfs` загружает его в `corporate-processed/reports/companies_by_city.csv`. Повторная загрузка использует тот же object key и заменяет текущий объект новым результатом.

## Поток данных

```text
PostgreSQL → Extract → Transform → Load CSV → upload_to_rustfs → RustFS PROCESSED
                                      └──────────────────────────────→ локальный CSV
PostgreSQL → data/raw/companies.csv → RustFS RAW
```

## Запуск

Из корня проекта в PowerShell:

```powershell
Copy-Item .env.example .env
```

Откройте `.env`, замените значения на локальные ключи RustFS, затем запустите:

```powershell
docker compose up -d db
docker compose up -d rustfs
docker compose up -d --force-recreate airflow
docker compose ps
```

В RustFS Console создайте два бакета: `corporate-raw` и `corporate-processed`. В `corporate-raw` загрузите `data/raw/companies.csv` с object key `companies/companies.csv`.

После выполнения DAG `corporate_etl` в интерфейсе Airflow проверьте четыре задачи со статусом `success`. В журнале `upload_to_rustfs` будет сообщение о загрузке. В RustFS Console откройте `corporate-processed/reports/companies_by_city.csv`.

Для ручной загрузки уже созданного отчёта с компьютера:

```powershell
python -m pip install boto3
python scripts/upload_to_rustfs.py
```

Скрипт читает локальный `.env` без дополнительной библиотеки. Он использует `localhost:9000`, потому что запускается на компьютере. Задача Airflow использует `rustfs:9000`, потому что обращается к RustFS из сети Docker Compose.

## Проверка обновления

Добавьте запись в PostgreSQL, например:

```sql
INSERT INTO companies (name, industry, city, employees)
SELECT 'Cloud Data Lab', 'IT', 'Tallinn', 175
WHERE NOT EXISTS (
    SELECT 1 FROM companies WHERE name = 'Cloud Data Lab'
);
```

Затем повторно запустите DAG. Показатели Tallinn в CSV и объекте PROCESSED должны обновиться.

## Контрольные вопросы

1. **Что такое объектное хранилище?** Хранилище, где данные представлены объектами с ключами и метаданными, а не файлами в традиционной файловой системе.
2. **Что такое bucket?** Логический контейнер объектов.
3. **Что такое object?** Сохраняемые данные и связанные с ними метаданные.
4. **Что такое key?** Уникальное имя объекта внутри бакета, например `companies/companies.csv`.
5. **Чем оно отличается от файловой системы?** Обращение идет к объектам по ключам через API; каталоги обычно являются частью ключа, а не реальными папками.
6. **Для чего RustFS?** Для S3-совместимого объектного хранения исходных и обработанных наборов данных.
7. **Что означает S3-совместимость?** RustFS поддерживает API и клиентские библиотеки экосистемы Amazon S3, например boto3.
8. **Чем RustFS отличается от PostgreSQL?** PostgreSQL хранит структурированные записи и позволяет выполнять SQL-запросы; RustFS хранит файлы и другие объекты.
9. **Что такое Data Lake?** Организованное хранилище исходных и подготовленных наборов данных для дальнейшей обработки и анализа.
10. **Что помещают в RAW?** Данные в исходном или почти исходном виде.
11. **Зачем хранить исходные данные?** Чтобы повторить обработку и получить новый результат, не извлекая исходные данные заново.
12. **Что помещают в PROCESSED?** Очищенные, преобразованные или агрегированные данные.
13. **Зачем разделять RAW и PROCESSED?** Чтобы сохранять происхождение и исходный вид данных, отделяя их от результатов обработки.
14. **Чем отличаются бакеты?** `corporate-raw` содержит экспорт таблицы, `corporate-processed` — отчет по городам.
15. **Для чего порт 9000?** Для S3 API.
16. **Для чего порт 9001?** Для веб-консоли RustFS.
17. **Почему Python использует localhost, а Airflow — rustfs?** Python запускается на хосте; Airflow — в сети Compose, где сервис доступен по имени `rustfs`.
18. **Для чего volume `rustfs_data`?** Для сохранения объектов при пересоздании контейнера RustFS.
19. **Как связаны Airflow и RustFS?** Airflow формирует CSV и передает его в RustFS через S3 API с помощью boto3.
20. **Что произойдет при ошибке `upload_to_rustfs`?** Эта задача завершится ошибкой; DAG не будет успешным, ошибка и журнал останутся в Airflow, а предыдущий объект в бакете не обновится.
