"""Centrality calculations used to rank airports for intervention."""

from __future__ import annotations

import networkx as nx
import pandas as pd


def compute_centralities(graph: nx.Graph) -> pd.DataFrame:
    """Return one row per node with all four required centrality measures."""

    if graph.number_of_nodes() == 0:
        raise ValueError("graph must contain at least one node")
    values = {
        "degree": nx.degree_centrality(graph),
        "closeness": nx.closeness_centrality(graph),
        "betweenness": nx.betweenness_centrality(graph, normalized=True),
        "eigenvector": nx.eigenvector_centrality(graph, max_iter=1000),
    }
    table = pd.DataFrame(values)
    table.index.name = "airport_id"
    return table.reset_index()


def rank_nodes(table: pd.DataFrame, strategy: str) -> list[int]:
    """Return node IDs sorted from most to least important for a strategy."""

    allowed = {"degree", "closeness", "betweenness", "eigenvector"}
    if strategy not in allowed:
        raise ValueError(f"strategy must be one of {sorted(allowed)}")
    if "airport_id" not in table or strategy not in table:
        raise ValueError("centrality table is missing required columns")
    return (
        table.sort_values([strategy, "airport_id"], ascending=[False, True])["airport_id"]
        .astype(int)
        .tolist()
    )
