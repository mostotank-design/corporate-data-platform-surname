"""Explore the companies CSV with DuckDB SQL."""
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
CSV_FILE = ROOT / "data" / "raw" / "companies.csv"


def sql_path(path: Path) -> str:
    return str(path).replace("\\", "/").replace("'", "''")


def show_result(connection, title: str, query: str) -> None:
    cursor = connection.execute(query)
    columns = [item[0] for item in cursor.description]
    rows = cursor.fetchall()
    print(f"\n{title}")
    print(" | ".join(columns))
    for row in rows:
        print(" | ".join(str(value) for value in row))


def main() -> None:
    if not CSV_FILE.is_file():
        raise FileNotFoundError(f"Не найден исходный файл: {CSV_FILE}")

    con = duckdb.connect()
    try:
        print(con.execute(
            "SELECT 'Corporate Data Platform' AS project, 10 + 15 AS result"
        ).fetchall())

        source = f"read_csv_auto('{sql_path(CSV_FILE)}')"
        show_result(con, "Все организации", f"SELECT * FROM {source}")
        show_result(
            con,
            "Организации с численностью более 200",
            f"SELECT name, industry, city, employees FROM {source} "
            "WHERE employees > 200 ORDER BY employees DESC",
        )
        show_result(
            con,
            "Организации с численностью не менее 200",
            f"SELECT name, city, employees FROM {source} "
            "WHERE employees >= 200 ORDER BY employees DESC LIMIT 5",
        )
        show_result(
            con,
            "Три крупнейшие организации с численностью не менее 150",
            f"SELECT name, industry, employees FROM {source} "
            "WHERE employees >= 150 ORDER BY employees DESC LIMIT 3",
        )
    finally:
        con.close()


if __name__ == "__main__":
    main()
