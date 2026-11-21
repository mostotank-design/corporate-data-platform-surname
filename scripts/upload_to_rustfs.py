"""Upload the latest local ETL report to the RustFS PROCESSED bucket."""

import os
from pathlib import Path

import boto3
from botocore.config import Config

project_root = Path(__file__).resolve().parents[1]
file_path = project_root / "airflow" / "output" / "companies_by_city.csv"

if not file_path.is_file():
    raise FileNotFoundError(
        f"Файл не найден: {file_path}. Сначала выполните DAG из работы № 9."
    )

client = boto3.client(
    "s3",
    endpoint_url=os.getenv("RUSTFS_ENDPOINT", "http://localhost:9000"),
    aws_access_key_id=os.getenv("RUSTFS_ACCESS_KEY", "rustfsadmin"),
    aws_secret_access_key=os.getenv("RUSTFS_SECRET_KEY", "rustfssecret123"),
    region_name="us-east-1",
    config=Config(s3={"addressing_style": "path"}),
)

bucket_name = os.getenv("RUSTFS_PROCESSED_BUCKET", "corporate-processed")
object_name = "reports/companies_by_city.csv"
client.upload_file(
    str(file_path),
    bucket_name,
    object_name,
    ExtraArgs={"ContentType": "text/csv"},
)
print(f"Загружено: {bucket_name}/{object_name}")
