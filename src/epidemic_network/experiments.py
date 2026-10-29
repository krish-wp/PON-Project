"""Reproducible experiment runners for closure-budget comparisons."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

import networkx as nx
import pandas as pd

from .centrality import compute_centralities
from .closures import STRATEGIES, remove_closed_nodes, select_closed_nodes
from .config import ModelConfig
from .metrics import epidemic_metrics, resilience_metrics
from .sir import metapopulation_sir_euler
from .synthetic import generate_comparison_networks
from .synthetic import degree_preserving_randomization


def _default_seed_node(graph: nx.Graph) -> object:
    return max(graph.nodes, key=lambda node: (graph.degree(node), str(node)))


def run_closure_budget_experiment(
    graph: nx.Graph,
    config: ModelConfig,
    *,
    budgets: Iterable[float] = tuple(index / 100 for index in range(1, 21)),
    strategies: Sequence[str] = STRATEGIES,
    random_trials: int = 5,
    seed: int = 2026,
    seed_nodes: Sequence[object] | None = None,
) -> pd.DataFrame:
    """Run comparable epidemic and resilience trials for closure budgets.

    Centrality strategies are deterministic for a fixed graph. Random closure
    uses ``random_trials`` independent selections at each budget.
    """

    if graph.number_of_nodes() == 0:
        raise ValueError("graph must contain at least one node")
    if random_trials < 1:
        raise ValueError("random_trials must be at least one")
    invalid = set(strategies) - set(STRATEGIES)
    if invalid:
        raise ValueError(f"unknown strategies: {sorted(invalid)}")
    centralities = compute_centralities(graph)
    fixed_seed_nodes = list(seed_nodes) if seed_nodes is not None else [_default_seed_node(graph)]
    if not fixed_seed_nodes or any(node not in graph for node in fixed_seed_nodes):
        raise ValueError("seed_nodes must contain at least one node from graph")
    rows: list[dict[str, float | int | str]] = []
    for budget in budgets:
        if not 0 < budget <= 1:
            raise ValueError("every budget must be in the interval (0, 1]")
        for strategy in strategies:
            trial_count = random_trials if strategy == "random" else 1
            for trial in range(trial_count):
                closed = select_closed_nodes(
                    graph,
                    strategy,
                    budget,
                    centralities=centralities,
                    seed=seed + trial,
                    excluded_nodes=fixed_seed_nodes,
                )
                remaining = remove_closed_nodes(graph, closed)
                if remaining.number_of_nodes() == 0:
                    continue
                simulation_seeds = fixed_seed_nodes
                epidemic = epidemic_metrics(
                    metapopulation_sir_euler(remaining, config, seed_nodes=simulation_seeds)
                )
                rows.append(
                    {
                        "strategy": strategy,
                        "budget": budget,
                        "trial": trial,
                        "closed_nodes": len(closed),
                        **epidemic,
                        **resilience_metrics(remaining),
                    }
                )
    return pd.DataFrame(rows).sort_values(["strategy", "budget", "trial"]).reset_index(drop=True)


def aggregate_experiment_results(results: pd.DataFrame) -> pd.DataFrame:
    """Aggregate repeated trials while retaining uncertainty information."""

    required = {"strategy", "budget", "final_infected_fraction", "peak_infected_fraction"}
    missing = required - set(results.columns)
    if missing:
        raise ValueError(f"results are missing columns: {sorted(missing)}")
    numeric = [
        "final_infected_fraction",
        "peak_infected_fraction",
        "time_to_peak",
        "largest_component_fraction",
        "connected_components",
        "average_degree",
    ]
    available = [column for column in numeric if column in results]
    grouped = results.groupby(["strategy", "budget"], as_index=False).agg(
        {column: ["mean", "std"] for column in available}
    )
    grouped.columns = [
        "strategy",
        "budget",
        *[f"{column}_{statistic}" for column in available for statistic in ("mean", "std")],
    ]
    return grouped.reset_index(drop=True)


def run_delayed_intervention_experiment(
    graph: nx.Graph,
    config: ModelConfig,
    *,
    strategy: str = "betweenness",
    budget: float = 0.10,
    intervention_times: Sequence[float] = (0.0, 5.0, 10.0),
    seed: int = 2026,
) -> pd.DataFrame:
    """Compare immediate and delayed closure for one fixed strategy/budget."""

    centralities = compute_centralities(graph)
    fixed_seed = _default_seed_node(graph)
    closed = select_closed_nodes(
        graph,
        strategy,
        budget,
        centralities=centralities,
        seed=seed,
        excluded_nodes=(fixed_seed,),
    )
    remaining = remove_closed_nodes(graph, closed)
    rows: list[dict[str, float | int | str]] = []
    for intervention_time in intervention_times:
        result = metapopulation_sir_euler(
            graph,
            config,
            seed_nodes=[fixed_seed],
            closed_nodes=closed,
            intervention_time=intervention_time,
        )
        rows.append(
            {
                "strategy": strategy,
                "budget": budget,
                "intervention_time": intervention_time,
                "closed_nodes": len(closed),
                **epidemic_metrics(result),
                **resilience_metrics(remaining),
            }
        )
    return pd.DataFrame(rows)


def run_synthetic_network_comparison(
    node_count: int,
    average_degree: float,
    config: ModelConfig,
    *,
    budget: float = 0.10,
    seed: int = 2026,
) -> pd.DataFrame:
    """Compare one representative closure budget across ER, BA, and WS graphs."""

    rows: list[dict[str, float | int | str]] = []
    for network_name, graph in generate_comparison_networks(
        node_count,
        average_degree,
        seed=seed,
    ).items():
        centralities = compute_centralities(graph)
        fixed_seed = _default_seed_node(graph)
        for strategy in ("random", "degree"):
            closed = select_closed_nodes(
                graph,
                strategy,
                budget,
                centralities=centralities,
                seed=seed,
                excluded_nodes=(fixed_seed,),
            )
            remaining = remove_closed_nodes(graph, closed)
            result = metapopulation_sir_euler(
                remaining,
                config,
                seed_nodes=[fixed_seed],
            )
            rows.append(
                {
                    "network_model": network_name,
                    "strategy": strategy,
                    "budget": budget,
                    "closed_nodes": len(closed),
                    **epidemic_metrics(result),
                    **resilience_metrics(remaining),
                }
            )
    return pd.DataFrame(rows)


def run_degree_preserving_comparison(
    graph: nx.Graph,
    config: ModelConfig,
    *,
    budget: float = 0.10,
    random_trials: int = 5,
    seed: int = 2026,
) -> pd.DataFrame:
    """Compare the real graph with a degree-preserving randomized graph."""

    randomized = degree_preserving_randomization(
        graph,
        swaps=10 * graph.number_of_edges(),
        seed=seed,
    )
    rows: list[dict[str, float | int | str]] = []
    for network_name, network in (("OpenFlights", graph), ("Degree-preserving", randomized)):
        centralities = compute_centralities(network)
        fixed_seed = _default_seed_node(network)
        for strategy in ("random", "degree"):
            trials = random_trials if strategy == "random" else 1
            for trial in range(trials):
                closed = select_closed_nodes(
                    network,
                    strategy,
                    budget,
                    centralities=centralities,
                    seed=seed + trial,
                    excluded_nodes=(fixed_seed,),
                )
                remaining = remove_closed_nodes(network, closed)
                result = metapopulation_sir_euler(
                    remaining,
                    config,
                    seed_nodes=[fixed_seed],
                )
                rows.append(
                    {
                        "network_model": network_name,
                        "strategy": strategy,
                        "budget": budget,
                        "trial": trial,
                        "closed_nodes": len(closed),
                        **epidemic_metrics(result),
                        **resilience_metrics(remaining),
                    }
                )
    return pd.DataFrame(rows)
