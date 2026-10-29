"""OpenFlights parsing and graph construction utilities."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

import networkx as nx


def _read_rows(path: Path) -> Iterable[list[str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        yield from csv.reader(handle)


def load_airports(path: str | Path) -> dict[int, dict[str, object]]:
    """Read an OpenFlights airports.dat file keyed by numeric airport ID."""

    airports: dict[int, dict[str, object]] = {}
    for row in _read_rows(Path(path)):
        if len(row) < 14:
            continue
        try:
            airport_id = int(row[0])
            latitude = float(row[6])
            longitude = float(row[7])
        except (TypeError, ValueError):
            continue
        airports[airport_id] = {
            "name": row[1],
            "city": row[2],
            "country": row[3],
            "iata": row[4],
            "icao": row[5],
            "latitude": latitude,
            "longitude": longitude,
        }
    return airports


def load_routes(path: str | Path) -> list[tuple[int, int]]:
    """Read valid numeric route endpoint IDs from an OpenFlights routes.dat file."""

    routes: list[tuple[int, int]] = []
    for row in _read_rows(Path(path)):
        if len(row) < 6:
            continue
        try:
            source_id = int(row[3])
            destination_id = int(row[5])
        except (TypeError, ValueError):
            continue
        if source_id != destination_id:
            routes.append((source_id, destination_id))
    return routes


def build_airport_graph(
    airports: dict[int, dict[str, object]],
    routes: Iterable[tuple[int, int]],
) -> nx.Graph:
    """Build a cleaned undirected graph from airport attributes and route pairs."""

    graph = nx.Graph()
    graph.add_nodes_from((airport_id, attributes) for airport_id, attributes in airports.items())
    valid_nodes = set(airports)
    graph.add_edges_from(
        (source, destination)
        for source, destination in routes
        if source in valid_nodes and destination in valid_nodes and source != destination
    )
    graph.remove_nodes_from(list(nx.isolates(graph)))
    return graph


def load_openflights_graph(
    airports_path: str | Path,
    routes_path: str | Path,
) -> nx.Graph:
    """Load, clean, and return an OpenFlights airport graph."""

    return build_airport_graph(load_airports(airports_path), load_routes(routes_path))


def graph_summary(graph: nx.Graph) -> dict[str, float | int]:
    """Return report-ready basic graph statistics."""

    if graph.number_of_nodes() == 0:
        raise ValueError("graph must contain at least one node")
    largest_component = max(nx.connected_components(graph), key=len)
    summary: dict[str, float | int] = {
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "average_degree": 2 * graph.number_of_edges() / graph.number_of_nodes(),
        "density": nx.density(graph),
        "connected_components": nx.number_connected_components(graph),
        "largest_component_nodes": len(largest_component),
        "isolated_nodes": sum(1 for node in graph if graph.degree(node) == 0),
        "average_clustering": nx.average_clustering(graph),
    }
    return summary


def largest_connected_component(graph: nx.Graph) -> nx.Graph:
    """Return a copy containing only the largest connected component."""

    if graph.number_of_nodes() == 0:
        raise ValueError("graph must contain at least one node")
    component = max(nx.connected_components(graph), key=len)
    return graph.subgraph(component).copy()
