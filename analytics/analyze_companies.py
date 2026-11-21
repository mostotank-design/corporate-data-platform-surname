"""Aggregate corporate data and write a CSV report and conclusions."""
import csv
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
CSV_FILE = ROOT / "data" / "raw" / "companies.csv"
REPORT_DIR = ROOT / "analytics" / "reports"
CITY_REPORT = REPORT_DIR / "city_analytics.csv"
CONCLUSIONS = REPORT_DIR / "conclusions.md"


def sql_path(path: Path) -> str:
    return str(path).replace("\\", "/").replace("'", "''")


def run_query(con, title: str, query: str):
    cursor = con.execute(query)
    columns = [item[0] for item in cursor.description]
    rows = cursor.fetchall()
    print(f"\n{title}")
    print(" | ".join(columns))
    for row in rows:
        print(" | ".join(str(value) for value in row))
    return columns, rows


def main() -> None:
    if not CSV_FILE.is_file():
        raise FileNotFoundError(f"Не найден исходный файл: {CSV_FILE}")

    con = duckdb.connect()
    try:
        con.execute(
            "CREATE VIEW companies AS "
            f"SELECT * FROM read_csv_auto('{sql_path(CSV_FILE)}')"
        )
        print("Данные подключены из", CSV_FILE.relative_to(ROOT))

        run_query(
            con,
            "Общие показатели",
            """SELECT COUNT(*) AS company_count,
                      SUM(employees) AS total_employees,
                      ROUND(AVG(employees), 2) AS avg_employees,
                      MAX(employees) AS max_employees,
                      MIN(employees) AS min_employees
               FROM companies""",
        )
        run_query(
            con,
            "Анализ по городам",
            """SELECT city, COUNT(*) AS company_count,
                      SUM(employees) AS total_employees,
                      ROUND(AVG(employees), 2) AS avg_employees,
                      MAX(employees) AS max_employees
               FROM companies
               GROUP BY city
               ORDER BY total_employees DESC""",
        )
        run_query(
            con,
            "Анализ по отраслям",
            """SELECT industry, COUNT(*) AS company_count,
                      SUM(employees) AS total_employees,
                      ROUND(AVG(employees), 2) AS avg_employees
               FROM companies
               GROUP BY industry
               ORDER BY total_employees DESC""",
        )
        run_query(
            con,
            "Города с суммарной численностью не менее 300",
            """SELECT city, COUNT(*) AS company_count,
                      SUM(employees) AS total_employees
               FROM companies
               GROUP BY city
               HAVING SUM(employees) >= 300
               ORDER BY total_employees DESC""",
        )

        _, most_companies_industry = run_query(
            con,
            "Отрасль с наибольшим количеством организаций",
            """SELECT industry, COUNT(*) AS company_count
               FROM companies
               GROUP BY industry
               ORDER BY company_count DESC, industry
               LIMIT 1""",
        )
        _, largest_city = run_query(
            con,
            "Город с наибольшей суммарной численностью сотрудников",
            """SELECT city, SUM(employees) AS total_employees
               FROM companies
               GROUP BY city
               ORDER BY total_employees DESC
               LIMIT 1""",
        )
        _, largest_company = run_query(
            con,
            "Крупнейшая организация",
            """SELECT name, city, industry, employees
               FROM companies
               ORDER BY employees DESC, name
               LIMIT 1""",
        )
        _, cities_with_two = run_query(
            con,
            "Города, в которых не менее двух организаций",
            """SELECT city, COUNT(*) AS company_count
               FROM companies
               GROUP BY city
               HAVING COUNT(*) >= 2
               ORDER BY company_count DESC, city""",
        )
        _, highest_average_industry = run_query(
            con,
            "Отрасль с максимальной средней численностью",
            """SELECT industry, ROUND(AVG(employees), 2) AS avg_employees
               FROM companies
               GROUP BY industry
               ORDER BY avg_employees DESC, industry
               LIMIT 1""",
        )

        city_columns, city_rows = run_query(
            con,
            "Итоговый аналитический отчет",
            """SELECT city, COUNT(*) AS company_count,
                      SUM(employees) AS total_employees,
                      ROUND(AVG(employees), 2) AS avg_employees,
                      MAX(employees) AS max_employees
               FROM companies
               GROUP BY city
               ORDER BY total_employees DESC""",
        )

        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        with CITY_REPORT.open("w", newline="", encoding="utf-8-sig") as report:
            writer = csv.writer(report)
            writer.writerow(city_columns)
            writer.writerows(city_rows)
        print(f"\nОтчет сохранен: {CITY_REPORT.relative_to(ROOT)}")

        industry = most_companies_industry[0][0] if most_companies_industry else "нет данных"
        industry_count = most_companies_industry[0][1] if most_companies_industry else 0
        city = largest_city[0][0] if largest_city else "нет данных"
        city_total = largest_city[0][1] if largest_city else 0
        company = largest_company[0][0] if largest_company else "нет данных"
        company_city = largest_company[0][1] if largest_company else "—"
        company_employees = largest_company[0][3] if largest_company else 0
        avg_industry = highest_average_industry[0][0] if highest_average_industry else "нет данных"
        avg_value = highest_average_industry[0][1] if highest_average_industry else 0
        cities_text = (
            ", ".join(f"{row[0]} ({row[1]})" for row in cities_with_two)
            if cities_with_two
            else "нет городов с двумя и более организациями"
        )

        CONCLUSIONS.write_text(
            "# Аналитический отчет корпоративной системы\n\n"
            "## Источник данных\n"
            "`data/raw/companies.csv` — исходные записи организаций.\n\n"
            "## Используемый инструмент\n"
            "DuckDB; запросы выполняются непосредственно к CSV без предварительного "
            "импорта в PostgreSQL.\n\n"
            "## Основные выводы\n"
            f"1. Больше всего организаций в отрасли «{industry}» — {industry_count}.\n"
            f"2. Наибольшая суммарная численность сотрудников в городе {city} — {city_total}.\n"
            f"3. Крупнейшая организация — «{company}» ({company_city}), "
            f"{company_employees} сотрудников.\n"
            f"4. Города с не менее чем двумя организациями: {cities_text}.\n"
            f"5. Наибольшая средняя численность в отрасли «{avg_industry}» — {avg_value}.\n\n"
            "## Ограничения анализа\n"
            "Численность сотрудников сама по себе не позволяет оценить выручку, "
            "прибыльность, производительность труда или финансовую устойчивость. "
            "Результаты относятся к снимку данных в CSV и могут отличаться от "
            "текущей PostgreSQL, если файл не обновлялся.\n",
            encoding="utf-8",
        )
        print(f"Выводы сохранены: {CONCLUSIONS.relative_to(ROOT)}")
    finally:
        con.close()


if __name__ == "__main__":
    main()
