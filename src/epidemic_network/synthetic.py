"""Synthetic and degree-preserving comparison networks."""

from __future__ import annotations

import networkx as nx


def generate_comparison_networks(
    node_count: int,
    average_degree: float,
    *,
    seed: int,
) -> dict[str, nx.Graph]:
    """Generate representative ER, BA, and WS graphs."""

    if node_count < 4 or average_degree <= 0:
        raise ValueError("node_count must be at least four and average_degree must be positive")
    degree = max(1, round(average_degree))
    ba_parameter = min(degree, node_count - 1)
    ws_parameter = min(degree if degree % 2 == 0 else degree + 1, node_count - 1)
    if ws_parameter < 2:
        ws_parameter = 2
    return {
        "ER": nx.gnp_random_graph(node_count, min(1.0, average_degree / (node_count - 1)), seed=seed),
        "BA": nx.barabasi_albert_graph(node_count, max(1, min(ba_parameter, node_count - 1)), seed=seed),
        "WS": nx.watts_strogatz_graph(node_count, ws_parameter, 0.1, seed=seed),
    }


def degree_preserving_randomization(
    graph: nx.Graph,
    *,
    swaps: int | None = None,
    seed: int | None = None,
) -> nx.Graph:
    """Return a graph with the same nodes/degrees after double-edge swaps."""

    if graph.number_of_edges() < 2:
        raise ValueError("at least two edges are required for degree-preserving randomization")
    result = graph.copy()
    requested_swaps = swaps if swaps is not None else 10 * result.number_of_edges()
    if requested_swaps < 0:
        raise ValueError("swaps must be non-negative")
    max_tries = max(100, requested_swaps * 20)
    nx.double_edge_swap(result, nswap=requested_swaps, max_tries=max_tries, seed=seed)
    return result
