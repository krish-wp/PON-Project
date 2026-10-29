import networkx as nx
import numpy as np

from epidemic_network.centrality import compute_centralities
from epidemic_network.closures import closure_count, remove_closed_nodes, select_closed_nodes
from epidemic_network.config import ModelConfig
from epidemic_network.experiments import (
    aggregate_experiment_results,
    run_closure_budget_experiment,
    run_degree_preserving_comparison,
    run_delayed_intervention_experiment,
    run_synthetic_network_comparison,
)
from epidemic_network.metrics import epidemic_metrics
from epidemic_network.network import build_airport_graph, largest_connected_component
from epidemic_network.sir import mean_field_sir_euler, metapopulation_sir_euler
from epidemic_network.synthetic import degree_preserving_randomization


def test_openflights_graph_is_cleaned() -> None:
    graph = build_airport_graph({1: {"name": "A"}, 2: {"name": "B"}, 3: {"name": "C"}}, [(1, 2), (2, 1), (1, 1)])
    assert set(graph.edges) == {(1, 2)}


def test_largest_connected_component_is_copied() -> None:
    graph = nx.disjoint_union(nx.path_graph(3), nx.path_graph(2))
    largest = largest_connected_component(graph)
    assert len(largest) == 3
    largest.remove_node(0)
    assert len(graph) == 5


def test_mean_field_sir_conserves_population() -> None:
    time, susceptible, infected, recovered = mean_field_sir_euler(
        0.3, 0.1, (0.99, 0.01, 0.0), duration=10.0, dt=0.01
    )
    assert len(time) == len(susceptible)
    assert np.allclose(susceptible + infected + recovered, 1.0)
    assert infected[-1] > infected[0]


def test_metapopulation_sir_conserves_each_node_population() -> None:
    graph = nx.path_graph(5)
    result = metapopulation_sir_euler(
        graph,
        ModelConfig(duration=5.0, dt=0.01, beta=0.2, gamma=0.1, mobility_rate=0.01),
    )
    assert np.allclose(result.total_population, result.total_population[0])
    assert np.all(result.susceptible >= 0)
    assert np.all(result.infected >= 0)
    assert np.all(result.recovered >= 0)


def test_closure_and_centrality_strategy() -> None:
    graph = nx.barabasi_albert_graph(20, 2, seed=3)
    table = compute_centralities(graph)
    closed = select_closed_nodes(graph, "degree", 0.10, centralities=table, excluded_nodes=(0,))
    assert len(closed) == closure_count(20, 0.10)
    assert 0 not in closed
    assert len(remove_closed_nodes(graph, closed)) == 18


def test_metrics_have_expected_keys() -> None:
    result = metapopulation_sir_euler(
        nx.path_graph(4),
        ModelConfig(duration=2.0, dt=0.01, beta=0.3, gamma=0.1),
    )
    metrics = epidemic_metrics(result)
    assert set(metrics) == {"final_infected_fraction", "peak_infected_fraction", "time_to_peak"}


def test_degree_preserving_randomization_preserves_degrees() -> None:
    graph = nx.cycle_graph(8)
    randomized = degree_preserving_randomization(graph, swaps=1, seed=1)
    assert sorted(dict(graph.degree).values()) == sorted(dict(randomized.degree).values())


def test_delayed_intervention_and_synthetic_comparison() -> None:
    graph = nx.barabasi_albert_graph(20, 2, seed=5)
    config = ModelConfig(duration=2.0, dt=0.01, beta=0.2, gamma=0.1, mobility_rate=0.01)
    delayed = run_delayed_intervention_experiment(
        graph,
        config,
        budget=0.10,
        intervention_times=(0.0, 1.0),
    )
    comparison = run_synthetic_network_comparison(20, 4.0, config, budget=0.10)
    assert len(delayed) == 2
    assert set(comparison["network_model"]) == {"ER", "BA", "WS"}


def test_degree_preserving_comparison_has_both_networks() -> None:
    graph = nx.barabasi_albert_graph(20, 2, seed=5)
    result = run_degree_preserving_comparison(
        graph,
        ModelConfig(duration=1.0, dt=0.01, beta=0.2, gamma=0.1),
        budget=0.10,
        random_trials=1,
        seed=2,
    )
    assert set(result["network_model"]) == {"OpenFlights", "Degree-preserving"}


def test_closure_budget_experiment_is_reproducible() -> None:
    graph = nx.barabasi_albert_graph(20, 2, seed=5)
    config = ModelConfig(duration=1.0, dt=0.01, beta=0.2, gamma=0.1, mobility_rate=0.01)
    kwargs = {
        "budgets": (0.10,),
        "strategies": ("random", "degree"),
        "random_trials": 2,
        "seed": 9,
    }
    first = run_closure_budget_experiment(graph, config, **kwargs)
    second = run_closure_budget_experiment(graph, config, **kwargs)
    assert first.equals(second)
    assert len(aggregate_experiment_results(first)) == 2
