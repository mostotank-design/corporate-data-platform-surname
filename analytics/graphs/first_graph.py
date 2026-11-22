"""Минимальный пример неориентированного графа NetworkX."""
import networkx as nx


def main() -> None:
    graph = nx.Graph()
    graph.add_node("company:1", node_type="company", label="Company A")
    graph.add_node("company:2", node_type="company", label="Company B")
    graph.add_node("city:Tallinn", node_type="city", label="Tallinn")
    graph.add_node("city:Riga", node_type="city", label="Riga")

    graph.add_edge("company:1", "city:Tallinn", relation="located_in")
    graph.add_edge("company:2", "city:Riga", relation="located_in")
    graph.add_edge("company:1", "company:2", relation="demo_relation")

    print("Количество вершин:", graph.number_of_nodes())
    print("Количество ребер:", graph.number_of_edges())
    print("\nВершины:")
    print(list(graph.nodes()))
    print("\nРебра:")
    print(list(graph.edges()))


if __name__ == "__main__":
    main()
