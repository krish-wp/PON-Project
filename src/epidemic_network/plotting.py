"""Publication-oriented plots for experiment CSV files."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from .experiments import aggregate_experiment_results
from .sir import mean_field_sir_euler


def plot_budget_results(results: pd.DataFrame, output: str | Path) -> None:
    """Plot final outbreak size and largest-component fraction by budget."""

    summary = aggregate_experiment_results(results)
    figure, axes = plt.subplots(1, 2, figsize=(10, 4), constrained_layout=True)
    for strategy, group in summary.groupby("strategy"):
        axes[0].plot(
            group["budget"] * 100,
            group["final_infected_fraction_mean"],
            marker="o",
            label=strategy,
        )
        axes[1].plot(
            group["budget"] * 100,
            group["largest_component_fraction_mean"],
            marker="o",
            label=strategy,
        )
    axes[0].set(
        xlabel="Closed airports (%)",
        ylabel="Final infected fraction",
        title="Epidemic outcome",
    )
    axes[1].set(
        xlabel="Closed airports (%)",
        ylabel="Largest component fraction",
        title="Network resilience",
    )
    for axis in axes:
        axis.grid(alpha=0.25)
    axes[1].legend(title="Strategy", fontsize=8)
    figure.savefig(output, dpi=200)
    plt.close(figure)


def plot_mean_field_threshold(
    beta_values: tuple[float, ...],
    gamma: float,
    output: str | Path,
) -> None:
    """Plot below-threshold, near-threshold, and above-threshold SIR curves."""

    figure, axes = plt.subplots(1, len(beta_values), figsize=(12, 3.5), sharey=True)
    for axis, beta in zip(axes, beta_values):
        time, susceptible, infected, recovered = mean_field_sir_euler(
            beta,
            gamma,
            (0.99, 0.01, 0.0),
            duration=40.0,
            dt=0.01,
        )
        axis.plot(time, susceptible, label="S")
        axis.plot(time, infected, label="I")
        axis.plot(time, recovered, label="R")
        axis.set_title(rf"$R_0={beta / gamma:.1f}$")
        axis.set_xlabel("Time")
        axis.grid(alpha=0.25)
    axes[0].set_ylabel("Fraction")
    axes[-1].legend(fontsize=8)
    figure.savefig(output, dpi=200)
    plt.close(figure)
