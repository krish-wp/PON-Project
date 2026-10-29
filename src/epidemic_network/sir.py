"""Mean-field and network metapopulation SIR integrators."""

from __future__ import annotations

from dataclasses import dataclass

import networkx as nx
import numpy as np

from .config import ModelConfig


@dataclass(frozen=True)
class MetapopulationResult:
    """Time series returned by the network SIR integrator."""

    time: np.ndarray
    susceptible: np.ndarray
    infected: np.ndarray
    recovered: np.ndarray
    nodes: tuple[object, ...]

    @property
    def total_population(self) -> np.ndarray:
        return self.susceptible.sum(axis=1) + self.infected.sum(axis=1) + self.recovered.sum(axis=1)

    @property
    def total_infected(self) -> np.ndarray:
        return self.infected.sum(axis=1)


def _time_grid(duration: float, dt: float) -> np.ndarray:
    steps = int(round(duration / dt))
    if not np.isclose(steps * dt, duration):
        raise ValueError("duration must be an integer multiple of dt")
    return np.linspace(0.0, duration, steps + 1)


def mean_field_sir_euler(
    beta: float,
    gamma: float,
    initial: tuple[float, float, float],
    *,
    duration: float,
    dt: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Integrate normalized mean-field SIR equations with explicit Euler steps."""

    if beta < 0 or gamma <= 0 or duration <= 0 or dt <= 0:
        raise ValueError("beta must be non-negative; gamma, duration, and dt must be positive")
    time = _time_grid(duration, dt)
    states = np.empty((len(time), 3), dtype=float)
    states[0] = initial
    if np.any(states[0] < 0) or not np.isclose(states[0].sum(), 1.0):
        raise ValueError("initial SIR state must be non-negative and sum to one")
    for index in range(len(time) - 1):
        susceptible, infected, recovered = states[index]
        derivative = np.array(
            [-beta * susceptible * infected,
             beta * susceptible * infected - gamma * infected,
             gamma * infected]
        )
        states[index + 1] = states[index] + dt * derivative
        if np.any(states[index + 1] < -1e-12):
            raise ValueError("Euler step produced a negative compartment; reduce dt")
        states[index + 1] = np.maximum(states[index + 1], 0.0)
        states[index + 1] /= states[index + 1].sum()
    return time, states[:, 0], states[:, 1], states[:, 2]


def _mobility_diffusion(
    values: np.ndarray,
    edge_sources: np.ndarray,
    edge_targets: np.ndarray,
    degrees: np.ndarray,
) -> np.ndarray:
    """Return an undirected graph diffusion term without a dense adjacency matrix."""

    neighbor_sum = np.bincount(
        edge_sources,
        weights=values[edge_targets],
        minlength=len(values),
    )
    neighbor_sum += np.bincount(
        edge_targets,
        weights=values[edge_sources],
        minlength=len(values),
    )
    return neighbor_sum - degrees * values


def metapopulation_sir_euler(
    graph: nx.Graph,
    config: ModelConfig,
    *,
    seed_nodes: list[object] | None = None,
    closed_nodes: list[object] | None = None,
    intervention_time: float | None = None,
) -> MetapopulationResult:
    """Integrate a metapopulation SIR system coupled by graph diffusion.

    Supplying ``closed_nodes`` and ``intervention_time`` enables a delayed
    intervention. At that time, closed airports stop generating new local
    infections and all incident mobility edges are removed. Their existing
    SIR populations remain and can recover.
    """

    if graph.number_of_nodes() == 0:
        raise ValueError("graph must contain at least one node")
    nodes = tuple(graph.nodes)
    node_count = len(nodes)
    node_index = {node: index for index, node in enumerate(nodes)}
    edge_indices = np.array(
        [(node_index[source], node_index[target]) for source, target in graph.edges],
        dtype=int,
    )
    if edge_indices.size:
        edge_sources = edge_indices[:, 0]
        edge_targets = edge_indices[:, 1]
    else:
        edge_sources = np.array([], dtype=int)
        edge_targets = np.array([], dtype=int)
    degrees = np.fromiter((graph.degree(node) for node in nodes), dtype=float, count=node_count)
    if closed_nodes is None and intervention_time is not None:
        raise ValueError("closed_nodes are required when intervention_time is supplied")
    if closed_nodes is not None and intervention_time is None:
        raise ValueError("intervention_time is required when closed_nodes are supplied")
    if intervention_time is not None and not 0 <= intervention_time <= config.duration:
        raise ValueError("intervention_time must lie within the simulation interval")
    unknown_closed = set(closed_nodes or []) - set(nodes)
    if unknown_closed:
        raise ValueError(f"closed nodes are not in graph: {sorted(unknown_closed)[:5]}")
    closed_indices = np.array(
        [node_index[node] for node in (closed_nodes or [])],
        dtype=int,
    )
    intervention_applied = False
    time = _time_grid(config.duration, config.dt)
    susceptible = np.empty((len(time), node_count), dtype=float)
    infected = np.empty_like(susceptible)
    recovered = np.zeros_like(susceptible)

    susceptible[0] = config.population_per_airport
    infected[0] = 0.0
    if seed_nodes is None:
        seed_nodes = [nodes[0]]
    unknown = set(seed_nodes) - set(nodes)
    if unknown:
        raise ValueError(f"seed nodes are not in graph: {sorted(unknown)[:5]}")
    seeded_amount = config.population_per_airport * config.initial_infected_fraction
    for node in seed_nodes:
        index = node_index[node]
        susceptible[0, index] -= seeded_amount
        infected[0, index] += seeded_amount

    for step in range(len(time) - 1):
        if intervention_time is not None and not intervention_applied and time[step] >= intervention_time:
            if closed_indices.size:
                active_edges = ~(
                    np.isin(edge_sources, closed_indices)
                    | np.isin(edge_targets, closed_indices)
                )
                edge_sources = edge_sources[active_edges]
                edge_targets = edge_targets[active_edges]
                degrees = np.bincount(
                    np.concatenate((edge_sources, edge_targets)),
                    minlength=node_count,
                ).astype(float)
            intervention_applied = True
        s = susceptible[step]
        i = infected[step]
        r = recovered[step]
        population = s + i + r
        local_infections = config.beta * s * i / np.maximum(population, 1e-15)
        if intervention_applied and closed_indices.size:
            local_infections[closed_indices] = 0.0
        new_recoveries = config.gamma * i
        mobility_s = config.mobility_rate * _mobility_diffusion(s, edge_sources, edge_targets, degrees)
        mobility_i = config.mobility_rate * _mobility_diffusion(i, edge_sources, edge_targets, degrees)
        mobility_r = config.mobility_rate * _mobility_diffusion(r, edge_sources, edge_targets, degrees)
        susceptible[step + 1] = s + config.dt * (-local_infections + mobility_s)
        infected[step + 1] = i + config.dt * (local_infections - new_recoveries + mobility_i)
        recovered[step + 1] = r + config.dt * (new_recoveries + mobility_r)
        if np.any(susceptible[step + 1] < -1e-10) or np.any(infected[step + 1] < -1e-10) or np.any(
            recovered[step + 1] < -1e-10
        ):
            raise ValueError("Euler step produced a negative compartment; reduce dt or mobility_rate")
        susceptible[step + 1] = np.maximum(susceptible[step + 1], 0.0)
        infected[step + 1] = np.maximum(infected[step + 1], 0.0)
        recovered[step + 1] = np.maximum(recovered[step + 1], 0.0)
    return MetapopulationResult(time, susceptible, infected, recovered, nodes)
