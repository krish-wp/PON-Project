"""Reproducible epidemic simulations on airport networks."""

from .config import ModelConfig
from .sir import MetapopulationResult, mean_field_sir_euler, metapopulation_sir_euler

__all__ = [
    "MetapopulationResult",
    "ModelConfig",
    "mean_field_sir_euler",
    "metapopulation_sir_euler",
]
