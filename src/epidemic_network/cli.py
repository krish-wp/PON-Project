"""Command-line entry points for the reproducible project workflow."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import networkx as nx
import pandas as pd

from .centrality import compute_centralities
from .closures import remove_closed_nodes, select_closed_nodes
from .config import ModelConfig
from .experiments import (
    run_closure_budget_experiment,
    run_degree_preserving_comparison,
    run_delayed_intervention_experiment,
    run_synthetic_network_comparison,
)
from .metrics import epidemic_metrics, resilience_metrics
from .network import graph_summary, largest_connected_component, load_openflights_graph
from .plotting import plot_budget_results, plot_mean_field_threshold
from .sir import mean_field_sir_euler, metapopulation_sir_euler


def run_smoke_test() -> dict[str, object]:
    """Run a fast end-to-end check without external data."""

    graph = nx.barabasi_albert_graph(40, 2, seed=42)
    centralities = compute_centralities(graph)
    closed = select_closed_nodes(graph, "betweenness", 0.10, centralities=centralities)
    remaining = remove_closed_nodes(graph, closed)
    config = ModelConfig(duration=20.0, dt=0.05, beta=0.35, gamma=0.10, mobility_rate=0.01)
    result = metapopulation_sir_euler(remaining, config)
    _, susceptible, infected, recovered = mean_field_sir_euler(
        config.beta,
        config.gamma,
        (0.99, 0.01, 0.0),
        duration=20.0,
        dt=0.05,
    )
    summary = {
        "original_graph": graph_summary(graph),
        "closed_nodes": len(closed),
        "remaining_graph": resilience_metrics(remaining),
        "epidemic": epidemic_metrics(result),
        "mean_field_final": {
            "susceptible": float(susceptible[-1]),
            "infected": float(infected[-1]),
            "recovered": float(recovered[-1]),
        },
    }
    return summary


def run_synthetic_experiment(output: Path) -> None:
    """Run a small reproducible closure-budget experiment."""

    graph = nx.barabasi_albert_graph(60, 2, seed=42)
    config = ModelConfig(duration=30.0, dt=0.05, beta=0.35, gamma=0.10, mobility_rate=0.01)
    results = run_closure_budget_experiment(
        graph,
        config,
        budgets=(0.01, 0.05, 0.10, 0.15, 0.20),
        random_trials=3,
        seed=42,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(output, index=False)
    print(f"Wrote {len(results)} rows to {output}")


def process_openflights(airports: Path, routes: Path, output_dir: Path) -> None:
    """Build the real graph and save summaries and centrality rankings."""

    graph = load_openflights_graph(airports, routes)
    largest = largest_connected_component(graph)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "source": {
            "airports_file": str(airports),
            "routes_file": str(routes),
        },
        "full_graph": graph_summary(graph),
        "largest_connected_component": graph_summary(largest),
    }
    (output_dir / "network_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    compute_centralities(largest).to_csv(output_dir / "centralities.csv", index=False)
    print(json.dumps(summary, indent=2))
    print(f"Wrote centrality rankings to {output_dir / 'centralities.csv'}")


def run_openflights_experiment(
    airports: Path,
    routes: Path,
    output: Path,
    *,
    duration: float,
    dt: float,
    random_trials: int,
    budgets: tuple[float, ...],
) -> None:
    """Run the configurable closure experiment on the largest real component."""

    graph = largest_connected_component(load_openflights_graph(airports, routes))
    config = ModelConfig(duration=duration, dt=dt)
    results = run_closure_budget_experiment(
        graph,
        config,
        budgets=budgets,
        random_trials=random_trials,
        seed=2026,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(output, index=False)
    print(f"Wrote {len(results)} rows to {output}")


def run_delayed_experiment(output: Path) -> None:
    """Run the compact delayed-intervention experiment on the real network."""

    graph = largest_connected_component(
        load_openflights_graph(Path("data/raw/airports.dat"), Path("data/raw/routes.dat"))
    )
    results = run_delayed_intervention_experiment(
        graph,
        ModelConfig(duration=20.0, dt=0.1),
        intervention_times=(0.0, 5.0, 10.0),
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(output, index=False)
    print(f"Wrote {len(results)} rows to {output}")


def run_synthetic_comparison(output: Path) -> None:
    """Run one compact ER/BA/WS comparison."""

    results = run_synthetic_network_comparison(
        100,
        10.0,
        ModelConfig(duration=20.0, dt=0.1),
        budget=0.10,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(output, index=False)
    print(f"Wrote {len(results)} rows to {output}")


def run_null_model_comparison(output: Path) -> None:
    """Run a compact degree-preserving null-model comparison."""

    graph = largest_connected_component(
        load_openflights_graph(Path("data/raw/airports.dat"), Path("data/raw/routes.dat"))
    )
    results = run_degree_preserving_comparison(
        graph,
        ModelConfig(duration=20.0, dt=0.1),
        budget=0.10,
        random_trials=3,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(output, index=False)
    print(f"Wrote {len(results)} rows to {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=[
            "smoke-test",
            "synthetic-experiment",
            "openflights-summary",
            "openflights-experiment",
            "delayed-experiment",
            "synthetic-comparison",
            "null-model-comparison",
            "mean-field-plot",
            "plot-results",
        ],
    )
    parser.add_argument("--output", type=Path, default=Path("results/synthetic_closure_results.csv"))
    parser.add_argument("--airports", type=Path, default=Path("data/raw/airports.dat"))
    parser.add_argument("--routes", type=Path, default=Path("data/raw/routes.dat"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--duration", type=float, default=80.0)
    parser.add_argument("--dt", type=float, default=0.05)
    parser.add_argument("--random-trials", type=int, default=5)
    parser.add_argument(
        "--budgets",
        type=str,
        default=",".join(f"{index / 100:.2f}" for index in range(1, 21)),
        help="Comma-separated closure fractions, e.g. 0.01,0.05,0.10",
    )
    args = parser.parse_args()
    if args.command == "smoke-test":
        print(json.dumps(run_smoke_test(), indent=2))
    elif args.command == "synthetic-experiment":
        run_synthetic_experiment(args.output)
    elif args.command == "openflights-summary":
        process_openflights(args.airports, args.routes, args.output_dir)
    elif args.command == "openflights-experiment":
        budgets = tuple(float(value.strip()) for value in args.budgets.split(",") if value.strip())
        run_openflights_experiment(
            args.airports,
            args.routes,
            args.output,
            duration=args.duration,
            dt=args.dt,
            random_trials=args.random_trials,
            budgets=budgets,
        )
    elif args.command == "delayed-experiment":
        run_delayed_experiment(args.output)
    elif args.command == "synthetic-comparison":
        run_synthetic_comparison(args.output)
    elif args.command == "null-model-comparison":
        run_null_model_comparison(args.output)
    elif args.command == "mean-field-plot":
        plot_mean_field_threshold((0.05, 0.10, 0.20), 0.10, args.output)
        print(f"Wrote plot to {args.output}")
    elif args.command == "plot-results":
        plot_budget_results(pd.read_csv(args.output), args.output.with_suffix(".png"))
        print(f"Wrote plot to {args.output.with_suffix('.png')}")


if __name__ == "__main__":
    main()
