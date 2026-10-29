"""Configuration objects shared by simulations and experiment runners."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelConfig:
    """Parameters for Euler-integrated SIR simulations."""

    beta: float = 0.30
    gamma: float = 0.10
    mobility_rate: float = 0.02
    dt: float = 0.05
    duration: float = 80.0
    population_per_airport: float = 1.0
    initial_infected_fraction: float = 0.01

    def __post_init__(self) -> None:
        if self.beta < 0 or self.gamma <= 0:
            raise ValueError("beta must be non-negative and gamma must be positive")
        if self.mobility_rate < 0 or self.dt <= 0 or self.duration <= 0:
            raise ValueError("mobility_rate, dt, and duration must be non-negative/positive")
        if self.population_per_airport <= 0:
            raise ValueError("population_per_airport must be positive")
        if not 0 < self.initial_infected_fraction < 1:
            raise ValueError("initial_infected_fraction must lie strictly between 0 and 1")

    @property
    def basic_reproduction_number(self) -> float:
        """Return the homogeneous SIR threshold parameter beta/gamma."""

        return self.beta / self.gamma
