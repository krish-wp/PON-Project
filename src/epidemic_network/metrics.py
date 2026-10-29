"""Metrics used to compare epidemic outcomes and network resilience."""

from __future__ import annotations

import networkx as nx
import numpy as np

from .sir import MetapopulationResult


def epidemic_metrics(result: MetapopulationResult) -> dict[str, float]:
    """Summarize final size, peak infection, and peak time."""

    infected = result.total_infected
    total_population = result.total_population
    infected_fraction = infected / np.maximum(total_population, 1e-15)
    peak_index = int(np.argmax(infected_fraction))
    return {
        "final_infected_fraction": float(result.recovered[-1].sum() / total_population[-1]),
        "peak_infected_fraction": float(infected_fraction[peak_index]),
        "time_to_peak": float(result.time[peak_index]),
    }


def resilience_metrics(graph: nx.Graph) -> dict[str, float | int]:
    """Summarize connectivity after an intervention."""

    node_count = graph.number_of_nodes()
    if node_count == 0:
        return {
            "remaining_nodes": 0,
            "remaining_edges": 0,
            "largest_component_fraction": 0.0,
            "connected_components": 0,
            "average_degree": 0.0,
        }
    largest = max((len(component) for component in nx.connected_components(graph)), default=0)
    return {
        "remaining_nodes": node_count,
        "remaining_edges": graph.number_of_edges(),
        "largest_component_fraction": largest / node_count,
        "connected_components": nx.number_connected_components(graph),
        "average_degree": 2 * graph.number_of_edges() / node_count,
    }
