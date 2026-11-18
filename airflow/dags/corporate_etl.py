"""Daily ETL report: company statistics grouped by city."""

import csv
import os
from datetime import datetime

import psycopg
from airflow.sdk import dag, task


@dag(
    dag_id="corporate_etl",
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["corporate-data", "etl"],
)
def corporate_etl():
    @task
    def extract_companies():
        connection = psycopg.connect(
            host=os.getenv("DB_HOST", "db"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "corporate"),
            user=os.getenv("DB_USER", "corporate_user"),
            password=os.getenv("DB_PASSWORD", "corporate_password"),
        )
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, name, industry, city, employees
                    FROM companies
                    ORDER BY id
                    """
                )
                rows = cursor.fetchall()
                return [
                    {
                        "id": row[0],
                        "name": row[1],
                        "industry": row[2],
                        "city": row[3],
                        "employees": row[4],
                    }
                    for row in rows
                ]
        finally:
            connection.close()

    @task
    def transform_companies(companies):
        cities = {}
        for company in companies:
            city = company["city"]
            employees = company["employees"]
            if city not in cities:
                cities[city] = {
                    "city": city,
                    "company_count": 0,
                    "total_employees": 0,
                }
            cities[city]["company_count"] += 1
            cities[city]["total_employees"] += employees

        result = []
        for city_data in cities.values():
            average = city_data["total_employees"] / city_data["company_count"]
            result.append(
                {
                    "city": city_data["city"],
                    "company_count": city_data["company_count"],
                    "total_employees": city_data["total_employees"],
                    "average_employees": round(average, 2),
                }
            )
        return sorted(result, key=lambda item: item["city"])

    @task
    def load_report(data):
        output_file = "/opt/airflow/output/companies_by_city.csv"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=[
                    "city",
                    "company_count",
                    "total_employees",
                    "average_employees",
                ],
            )
            writer.writeheader()
            writer.writerows(data)
        print(f"Report saved to {output_file}")
        print(f"Rows written: {len(data)}")
        return output_file

    extracted_data = extract_companies()
    transformed_data = transform_companies(extracted_data)
    load_report(transformed_data)


corporate_etl()
