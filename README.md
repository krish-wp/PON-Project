# Containing Epidemics on the Global Air-Transport Network

Group 22 — SC452

- Krish Dhola — 202301189
- Prince Sojitra — 202301126
- Jenish Vasani — 202301057

This repository contains the reproducible Python implementation for the project:

> **Containing Epidemics on the Global Air-Transport Network: Budget, Centrality, and the Epidemic Threshold**

The project studies random and centrality-based airport closures on a cleaned OpenFlights network. It validates the standard SIR epidemic threshold and provides a network metapopulation SIR model with mobility coupling.

## Repository layout

```text
data/
  raw/          OpenFlights source files (not committed)
  processed/    generated graph summaries/data (not committed)
report/         IEEE two-column LaTeX report
results/        generated experiment outputs and figures
src/
  epidemic_network/
    centrality.py
    closures.py
    config.py
    metrics.py
    network.py
    sir.py
    synthetic.py
    cli.py
tests/
```

## Setup

Use Python 3.11 or newer:

```powershell
& "C:\Users\Krish\AppData\Local\Programs\Python\Python311\python.exe" -m pip install -e ".[dev]"
```

## Smoke test

The smoke test uses a small synthetic network and does not require the OpenFlights files:

```powershell
& "C:\Users\Krish\AppData\Local\Programs\Python\Python311\python.exe" -m epidemic_network.cli smoke-test
```

## Process the real network

After placing `airports.dat` and `routes.dat` in `data/raw/`, generate the
network summary and centrality rankings:

```powershell
& "C:\Users\Krish\AppData\Local\Programs\Python\Python311\python.exe" -m epidemic_network.cli openflights-summary
```

Run the configurable real-network closure experiment and generate its plot:

```powershell
& "C:\Users\Krish\AppData\Local\Programs\Python\Python311\python.exe" -m epidemic_network.cli openflights-experiment --output results\openflights_closure_results.csv
& "C:\Users\Krish\AppData\Local\Programs\Python\Python311\python.exe" -m epidemic_network.cli plot-results --output results\openflights_closure_results.csv
```

For development, reduce the runtime with `--duration`, `--dt`, and
`--random-trials`; representative budgets can be selected with
`--budgets 0.01,0.05,0.10,0.15,0.20`. The final report must record the
exact values used.

Supporting analyses are available as separate commands:

```powershell
& "C:\Users\Krish\AppData\Local\Programs\Python\Python311\python.exe" -m epidemic_network.cli synthetic-comparison --output results\synthetic_network_comparison.csv
& "C:\Users\Krish\AppData\Local\Programs\Python\Python311\python.exe" -m epidemic_network.cli delayed-experiment --output results\delayed_intervention_results.csv
& "C:\Users\Krish\AppData\Local\Programs\Python\Python311\python.exe" -m epidemic_network.cli mean-field-plot --output results\mean_field_threshold.png
```

## OpenFlights data

Place the dated OpenFlights `airports.dat` and `routes.dat` files in `data/raw/`. The parser only uses valid numeric airport IDs and route endpoint IDs. Raw data is intentionally excluded from version control; record the source URL and access date in the final report.

## Research workflow

1. Run the smoke test and unit tests.
2. Add and document the OpenFlights snapshot.
3. Build the cleaned graph and compute centralities.
4. Run threshold, closure-budget, resilience, synthetic-network, null-model, and delayed-intervention experiments.
5. Generate figures/tables and compile `report/main.tex` with an IEEEtran installation.

All final results must be generated from recorded configuration values and fixed seeds. Do not report ungenerated or unverified results.
