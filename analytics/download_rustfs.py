"""Fallback: download RustFS objects with boto3, then analyze local CSV copies."""
import os
from getpass import getpass
from pathlib import Path

import boto3
import duckdb
from botocore.config import Config

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "data" / "processed"


def load_local_env() -> None:
    env_file = ROOT / ".env"
    if not env_file.is_file():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            name, value = line.split("=", 1)
            os.environ.setdefault(name.strip(), value.strip().strip('"').strip("'"))


def main() -> None:
    load_local_env()
    access_key = os.getenv("RUSTFS_ACCESS_KEY") or input("RustFS Access Key: ")
    secret_key = os.getenv("RUSTFS_SECRET_KEY") or getpass("RustFS Secret Key: ")

    client = boto3.client(
        "s3",
        endpoint_url="http://localhost:9000",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="us-east-1",
        config=Config(s3={"addressing_style": "path"}),
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    raw_file = OUTPUT_DIR / "companies.csv"
    processed_file = OUTPUT_DIR / "companies_by_city.csv"
    client.download_file("corporate-raw", "companies/companies.csv", str(raw_file))
    client.download_file(
        "corporate-processed",
        "reports/companies_by_city.csv",
        str(processed_file),
    )
    print(f"Скачаны объекты в {OUTPUT_DIR.relative_to(ROOT)}")

    con = duckdb.connect()
    try:
        for title, path in (("RAW", raw_file), ("PROCESSED", processed_file)):
            sql_path = str(path).replace("\\", "/").replace("'", "''")
            cursor = con.execute(f"SELECT * FROM read_csv_auto('{sql_path}')")
            print(f"\n{title}")
            print(" | ".join(item[0] for item in cursor.description))
            for row in cursor.fetchall():
                print(" | ".join(str(value) for value in row))

        raw_path = str(raw_file).replace("\\", "/").replace("'", "''")
        cursor = con.execute(
            f"""SELECT city, COUNT(*) AS company_count,
                       SUM(employees) AS total_employees
                FROM read_csv_auto('{raw_path}')
                GROUP BY city
                ORDER BY total_employees DESC"""
        )
        print("\nАнализ скачанных RAW-данных по городам")
        print(" | ".join(item[0] for item in cursor.description))
        for row in cursor.fetchall():
            print(" | ".join(str(value) for value in row))
    finally:
        con.close()


if __name__ == "__main__":
    main()
