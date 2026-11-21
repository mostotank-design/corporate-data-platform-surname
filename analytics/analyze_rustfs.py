"""Read and analyze RAW and PROCESSED objects from RustFS using DuckDB httpfs."""
import os
from getpass import getpass
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]


def load_local_env() -> None:
    env_file = ROOT / ".env"
    if not env_file.is_file():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            name, value = line.split("=", 1)
            os.environ.setdefault(name.strip(), value.strip().strip('"').strip("'"))


def sql_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def show_result(con, title: str, query: str) -> None:
    cursor = con.execute(query)
    columns = [item[0] for item in cursor.description]
    rows = cursor.fetchall()
    print(f"\n{title}")
    print(" | ".join(columns))
    for row in rows:
        print(" | ".join(str(value) for value in row))


def main() -> None:
    load_local_env()
    access_key = os.getenv("RUSTFS_ACCESS_KEY") or input("RustFS Access Key: ")
    secret_key = os.getenv("RUSTFS_SECRET_KEY") or getpass("RustFS Secret Key: ")

    con = duckdb.connect()
    try:
        try:
            con.execute("INSTALL httpfs")
            con.execute("LOAD httpfs")
        except Exception as exc:
            raise RuntimeError(
                "Не удалось установить или загрузить httpfs. "
                "Попробуйте альтернативу: python analytics/download_rustfs.py"
            ) from exc

        con.execute(
            f"""CREATE OR REPLACE SECRET rustfs_secret (
                TYPE s3,
                KEY_ID {sql_string(access_key)},
                SECRET {sql_string(secret_key)},
                REGION 'us-east-1',
                ENDPOINT 'localhost:9000',
                URL_STYLE 'path',
                USE_SSL false
            )"""
        )
        print("Подключение к RustFS настроено")

        raw = "s3://corporate-raw/companies/companies.csv"
        processed = "s3://corporate-processed/reports/companies_by_city.csv"
        show_result(con, "Данные из RAW", f"SELECT * FROM read_csv_auto('{raw}')")
        show_result(
            con,
            "Анализ RAW по городам",
            f"""SELECT city, COUNT(*) AS company_count,
                       SUM(employees) AS total_employees
                FROM read_csv_auto('{raw}')
                GROUP BY city
                ORDER BY total_employees DESC""",
        )
        show_result(
            con,
            "Данные из PROCESSED",
            f"SELECT * FROM read_csv_auto('{processed}')",
        )
        show_result(
            con,
            "Структура RAW",
            f"DESCRIBE SELECT * FROM read_csv_auto('{raw}')",
        )
        show_result(
            con,
            "Структура PROCESSED",
            f"DESCRIBE SELECT * FROM read_csv_auto('{processed}')",
        )
    finally:
        con.close()


if __name__ == "__main__":
    main()
