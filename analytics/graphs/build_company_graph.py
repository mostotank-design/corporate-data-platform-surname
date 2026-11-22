"""Построение и анализ графа корпоративных данных."""
from itertools import combinations
from pathlib import Path

import duckdb
import networkx as nx


ROOT = Path(__file__).resolve().parents[2]
DATA_FILE = ROOT / "data" / "raw" / "companies.csv"


def build_graph() -> tuple[nx.Graph, list[str]]:
    """Читает CSV через DuckDB и создает узлы компаний, городов и отраслей."""
    if not DATA_FILE.is_file():
        raise FileNotFoundError(f"Не найден исходный файл: {DATA_FILE}")

    graph = nx.Graph()
    con = duckdb.connect()
    try:
        rows = con.execute(
            "SELECT id, name, industry, city, employees "
            f"FROM read_csv_auto('{DATA_FILE.as_posix()}') "
            "ORDER BY id"
        ).fetchall()
    finally:
        con.close()

    company_nodes = []
    for company_id, name, industry, city, employees in rows:
        company_node = f"company:{company_id}"
        city_node = f"city:{city}"
        industry_node = f"industry:{industry}"

        graph.add_node(
            company_node,
            node_type="company",
            label=str(name),
            employees=int(employees),
        )
        graph.add_node(city_node, node_type="city", label=str(city))
        graph.add_node(
            industry_node, node_type="industry", label=str(industry)
        )
        graph.add_edge(company_node, city_node, relation="located_in")
        graph.add_edge(company_node, industry_node, relation="operates_in")
        company_nodes.append(company_node)

    return graph, company_nodes


def label(graph: nx.Graph, node: str) -> str:
    return str(graph.nodes[node]["label"])


def print_analysis(graph: nx.Graph, company_nodes: list[str]) -> None:
    print("Организаций в CSV:", len(company_nodes))
    print("Количество вершин графа:", graph.number_of_nodes())
    print("Количество ребер графа:", graph.number_of_edges())

    for node_type, title in (
        ("company", "Организации"),
        ("city", "Города"),
        ("industry", "Отрасли"),
    ):
        print(f"\n{title}:")
        for node, data in graph.nodes(data=True):
            if data["node_type"] == node_type:
                suffix = (
                    f" — {data['employees']} сотрудников"
                    if node_type == "company"
                    else ""
                )
                print(f"- {data['label']}{suffix}")

    print("\nСвязи организаций:")
    for node in company_nodes:
        neighbors = [
            f"{label(graph, neighbor)} ({graph.nodes[neighbor]['node_type']})"
            for neighbor in graph.neighbors(node)
        ]
        print(f"- {label(graph, node)}: {', '.join(neighbors)}")

    print("\nОрганизации по городам:")
    for node, data in graph.nodes(data=True):
        if data["node_type"] == "city":
            names = sorted(
                label(graph, neighbor)
                for neighbor in graph.neighbors(node)
                if graph.nodes[neighbor]["node_type"] == "company"
            )
            print(f"- {data['label']}: {', '.join(names)}")

    print("\nОрганизации по отраслям:")
    for node, data in graph.nodes(data=True):
        if data["node_type"] == "industry":
            names = sorted(
                label(graph, neighbor)
                for neighbor in graph.neighbors(node)
                if graph.nodes[neighbor]["node_type"] == "company"
            )
            print(f"- {data['label']}: {', '.join(names)}")

    print("\nОбщие города и отрасли организаций:")
    found_common = False
    for first, second in combinations(company_nodes, 2):
        common = sorted(set(graph.neighbors(first)) & set(graph.neighbors(second)))
        if common:
            found_common = True
            descriptions = ", ".join(
                f"{label(graph, node)} ({graph.nodes[node]['node_type']})"
                for node in common
            )
            print(f"- {label(graph, first)} ↔ {label(graph, second)}: {descriptions}")
    if not found_common:
        print("- Общих городов или отраслей нет.")

    print("\nСтепени вершин:")
    for node, degree in sorted(
        graph.degree(), key=lambda item: (-item[1], label(graph, item[0]))
    ):
        print(f"- {label(graph, node)} ({graph.nodes[node]['node_type']}): {degree}")

    print("\nНаиболее связанные вершины (с учетом равенства):")
    degrees = dict(graph.degree())
    max_degree = max(degrees.values(), default=0)
    for node in sorted(
        (node for node, degree in degrees.items() if degree == max_degree),
        key=lambda item: label(graph, item),
    ):
        print(f"- {label(graph, node)}: {max_degree}")

    degree_centrality = nx.degree_centrality(graph)
    top_degree = max(degree_centrality.values(), default=0)
    print("\nЦентральность по степени (максимальные значения):")
    for node in sorted(
        (node for node, value in degree_centrality.items() if value == top_degree),
        key=lambda item: label(graph, item),
    ):
        print(f"- {label(graph, node)}: {top_degree:.3f}")

    betweenness = nx.betweenness_centrality(graph)
    top_betweenness = max(betweenness.values(), default=0)
    print("\nПосредническая центральность (максимальные значения):")
    for node in sorted(
        (node for node, value in betweenness.items() if value == top_betweenness),
        key=lambda item: label(graph, item),
    ):
        print(f"- {label(graph, node)}: {top_betweenness:.3f}")

    components = sorted(
        nx.connected_components(graph), key=lambda component: (-len(component), sorted(component)[0])
    )
    print("\nКомпоненты связности:", len(components))
    for index, component in enumerate(components, start=1):
        print(f"- Компонента {index}: {len(component)} вершин")

    connected_pair = next(
        (
            (first, second)
            for first, second in combinations(company_nodes, 2)
            if nx.has_path(graph, first, second)
        ),
        None,
    )
    if connected_pair:
        first, second = connected_pair
        path = nx.shortest_path(graph, first, second)
        print("\nПример кратчайшего пути:")
        print(" → ".join(label(graph, node) for node in path))
        print("Длина пути:", len(path) - 1, "ребра")
    elif len(company_nodes) >= 2:
        print("\nМежду выбранными организациями нет пути.")

    print("\nПроверка совпадения города и отрасли:")
    both = []
    for first, second in combinations(company_nodes, 2):
        shared = set(graph.neighbors(first)) & set(graph.neighbors(second))
        if sum(graph.nodes[node]["node_type"] == "city" for node in shared) and sum(
            graph.nodes[node]["node_type"] == "industry" for node in shared
        ):
            both.append((label(graph, first), label(graph, second)))
    if both:
        for first, second in both:
            print(f"- {first} и {second}")
    else:
        print("- Таких пар организаций в исходном CSV нет.")


def get_graph() -> nx.Graph:
    """Совместимость с визуализатором из практической работы."""
    graph, _ = build_graph()
    return graph


def main() -> None:
    graph, company_nodes = build_graph()
    print_analysis(graph, company_nodes)


if __name__ == "__main__":
    main()
