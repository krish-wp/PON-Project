"""Airport closure strategies and graph-removal helpers."""

from __future__ import annotations

from collections.abc import Sequence
import math

import networkx as nx
import pandas as pd

from .centrality import rank_nodes


STRATEGIES = ("random", "degree", "closeness", "betweenness", "eigenvector")


def closure_count(node_count: int, budget: float) -> int:
    """Convert a fractional closure budget into a deterministic node count."""

    if node_count <= 0:
        raise ValueError("node_count must be positive")
    if not 0 < budget <= 1:
        raise ValueError("budget must be in the interval (0, 1]")
    return min(node_count, max(1, math.ceil(node_count * budget)))


def select_closed_nodes(
    graph: nx.Graph,
    strategy: str,
    budget: float,
    *,
    centralities: pd.DataFrame | None = None,
    seed: int | None = None,
    excluded_nodes: Sequence[int] = (),
) -> list[int]:
    """Select airports to close for one strategy and budget."""

    if strategy not in STRATEGIES:
        raise ValueError(f"strategy must be one of {STRATEGIES}")
    excluded = set(excluded_nodes)
    unknown = excluded - set(graph.nodes)
    if unknown:
        raise ValueError(f"excluded nodes are not in graph: {sorted(unknown)[:5]}")
    count = closure_count(graph.number_of_nodes(), budget)
    if count > graph.number_of_nodes() - len(excluded):
        raise ValueError("budget leaves too few eligible nodes after exclusions")
    eligible = [node for node in graph if node not in excluded]
    if strategy == "random":
        generator = __import__("random").Random(seed)
        return generator.sample(eligible, count)
    if centralities is None:
        raise ValueError("centralities are required for non-random strategies")
    return [node for node in rank_nodes(centralities, strategy) if node not in excluded][:count]


def remove_closed_nodes(graph: nx.Graph, closed_nodes: Sequence[int]) -> nx.Graph:
    """Return a copy with closed airports and their incident routes removed."""

    result = graph.copy()
    unknown = set(closed_nodes) - set(result.nodes)
    if unknown:
        raise ValueError(f"closed nodes are not in graph: {sorted(unknown)[:5]}")
    result.remove_nodes_from(closed_nodes)
    return result
