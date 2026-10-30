# Project Understanding: From Start to End

This document explains **everything** about the project — what we did, why we did it, and how we did it — from the very first step to the final report. It is written for deep understanding and viva preparation.

---

## 0. The Big Picture in One Sentence

> We used the real global airport network (OpenFlights) and ran an SIR epidemic simulation where infection spreads from airport to airport through flight routes, then tested which airports to close (under a limited budget) to stop the outbreak most effectively — comparing random closure against centrality-targeted closure (degree, closeness, betweenness, eigenvector).

---

## 1. WHY We Did This Project

### The Real-World Problem

Air travel connects distant populations. When an epidemic starts in one city, infected people fly to other cities and seed new outbreaks there. Airports become pathways for geographic spread.

**The naive idea:** Close all airports. **The problem:** This is unrealistic — it would stop trade, essential travel, emergency movement, and the global economy.

**The practical question:** If we can close only a *limited* number of airports (a "budget"), **which airports should we close first** to control the epidemic most effectively?

This is a **network problem** because airports and routes form a connected graph. The structure of the network determines how fast and how far an epidemic can spread.

### Our Contribution

We built a reproducible framework that:
1. Cleans real OpenFlights data into a network graph
2. Computes centrality scores for every airport
3. Simulates an SIR epidemic moving through the network (metapopulation model)
4. Closes airports using different strategies under equal budgets
5. Measures outbreak size, peak infection, and network damage
6. Compares strategies and draws conclusions

---

## 2. WHAT We Did (Pipeline Overview)

```
Step 1: Data          → airports.dat + routes.dat (OpenFlights)
Step 2: Network       → Clean graph: airports = nodes, routes = edges
Step 3: Centrality    → Degree, closeness, betweenness, eigenvector for every airport
Step 4: Epidemic Model→ SIR at every airport + movement between airports (metapopulation)
Step 5: Closure       → Close a fraction of airports using each strategy
Step 6: Simulate      → Run epidemic on remaining network
Step 7: Measure       → Final outbreak, peak infection, time to peak, LCC fraction
Step 8: Compare       → Random vs degree vs closeness vs betweenness vs eigenvector
Step 9: Report        → LaTeX report with results, figures, discussion
```

---

## 3. HOW We Did It (Step by Step)

### Step 1: Getting the Data

**Source:** OpenFlights dataset (public, downloaded 27 October 2026).

**Files:**
- `data/raw/airports.dat` — airport records (ID, name, city, country, lat/long)
- `data/raw/routes.dat` — route records (source ID, destination ID)
- `data/raw/SOURCE.txt` — records source URLs and access date

**Code:** `src/epidemic_network/network.py` → `load_airports()`, `load_routes()`

```python
# Each row in airports.dat → one airport record
# Each row in routes.dat → one directed route (source_id, destination_id)
# We treat routes as UNDIRECTED for this project
```

### Step 2: Building & Cleaning the Network Graph

**Airports = nodes, Routes = edges.**

**Cleaning (in `build_airport_graph()`):**
1. Remove rows with invalid numeric airport IDs
2. Remove self-loops (airport connected to itself)
3. Remove duplicate routes
4. Remove isolated airports (no connections)

**Result (full graph → largest component):**

| Measure | Full Graph | Largest Component |
|---------|-----------|-------------------|
| Airports | 3,214 | 3,188 |
| Routes | 18,858 | 18,833 |
| Average degree | — | 11.81 |
| Connected components | 7 | 1 |

**Why largest component only?** An epidemic can only spread *inside* a connected component. The largest component contains almost all airports, so it is the meaningful part for one global spreading experiment. The other 6 components are tiny and disconnected.

**Why undirected?** We assume if a route exists A→B, people can travel B→A too. Real flights are directed and weighted — this is a simplification and a stated limitation.

**Code:** `network.py` → `build_airport_graph()`, `largest_connected_component()`, `graph_summary()`

### Step 3: Computing Centrality Measures

Centrality answers: **"Which airports are structurally important?"**

We compute four measures for every airport using NetworkX:

| Centrality | Definition | Intuition for Closure |
|------------|-----------|----------------------|
| **Degree** | Number of direct connections | Close hubs with many direct routes |
| **Closeness** | Average shortest-path distance to all other airports | Close airports that can reach everyone quickly |
| **Betweenness** | Fraction of shortest paths passing through this airport | Close bridges between regions |
| **Eigenvector** | Connections to other important airports (recursive importance) | Close airports connected to influential neighbors |

**Top 3 airports by each measure (from `data/processed/centralities.csv`):**

| Measure | #1 | #2 | #3 |
|---------|----|----|----|
| Degree | Schiphol (580) | Frankfurt (340) | Charles de Gaulle (1382) |
| Closeness | Frankfurt (340) | Charles de Gaulle (1382) | Heathrow (507) |
| Betweenness | Charles de Gaulle (1382) | LAX (3484) | Anchorage (3774) |
| Eigenvector | Schiphol (580) | Frankfurt (340) | Charles de Gaulle (1382) |

**Why Anchorage (3774) for betweenness?** Many intercontinental shortest paths pass through high-latitude connections (polar routes). Anchorage acts as a bridge between regions — but being a bridge doesn't necessarily make it the best target for stopping infection spread.

**Why use several centralities?** There is no single universal definition of "important." A local hub, a global shortcut, and a regional bridge are all important in different ways. Comparing strategies lets the data show which type matters most for this epidemic model.

**Code:** `centrality.py` → `compute_centralities()`, `rank_nodes()`

### Step 4: The Epidemic Model (SIR + Metapopulation)

#### 4.1 Basic SIR Model (One Population)

Each airport's population is divided into three compartments:

- **S** = Susceptible (can become infected)
- **I** = Infected (currently infectious)
- **R** = Recovered (no longer infectious)

**Equations:**

```
dS/dt = -β * S * I
dI/dt =  β * S * I - γ * I
dR/dt =  γ * I
```

- **β (beta)** = infection/transmission rate = **0.30**
- **γ (gamma)** = recovery rate = **0.10**

**Epidemic Threshold: R₀**

```
R₀ = β * S₀ / γ
```

With β=0.30, γ=0.10, S₀≈1: **R₀ = 3 > 1**, so an outbreak **can grow**.

- R₀ < 1: each infected person infects <1 person → outbreak dies out
- R₀ > 1: each infected person infects >1 person → outbreak spreads

#### 4.2 Network Metapopulation Model (All Airports Connected)

The simple SIR model describes one isolated population. Our model is different:

**It runs an SIR system at EVERY airport**, and lets people move between connected airports.

**How infection spreads (two ways):**
1. **Local transmission** within an airport: `β * S_i * I_i / N_i`
2. **Network movement** along routes: people (including infected people) move between connected airports

**Mobility term** (for each compartment X at airport i):

```
mobility = μ * (Σ X_j - k_i * X_i)
```

- μ = mobility rate = **0.02** (how fast people move between airports)
- k_i = degree of airport i (number of routes)
- In plain terms: people leave airport i and arrive at its neighbours, carrying their infection status with them

**Simulation parameters (main sweep):**

| Parameter | Value | Meaning |
|-----------|-------|---------|
| β | 0.30 | Infection rate per contact |
| γ | 0.10 | Recovery rate |
| μ | 0.02 | Mobility rate between airports |
| dt | 0.1 | Time step (Euler integration) |
| Duration | 80 | Total simulation time |
| Population per airport | 1 | Normalized (all airports equal) |
| Initial infected | 1% | At one fixed high-degree seed airport |

**Method:** Explicit Euler integration — at every small time step, calculate change in S, I, R, then update values. We validated that dt=0.1 is stable (no negative compartments).

**Fairness rule:** The initial infected seed airport is **protected from closure**. Every strategy starts from the same initial infection. Otherwise a strategy could "win" simply by closing the airport where infection starts.

**Code:** `sir.py` → `mean_field_sir_euler()`, `metapopulation_sir_euler()`

### Step 5: Airport Closure Experiment

For each strategy, we close a fraction of airports and run the epidemic on the *remaining* network.

**Number of airports closed:**

```
count = ceil(budget × total airports)
```

Minimum 1 airport for any positive budget. Budgets tested: **1% to 20%** (every integer).

**Strategies compared:**

| Strategy | How airports are selected |
|----------|--------------------------|
| **Random** | Same number as budget, chosen randomly |
| **Degree** | Highest degree centrality first |
| **Closeness** | Highest closeness centrality first |
| **Betweenness** | Highest betweenness centrality first |
| **Eigenvector** | Highest eigenvector centrality first |

**Random trials:** Random closure is repeated **5 times** per budget because a single random draw could be unusually lucky or unlucky. Centrality strategies are deterministic (1 trial each).

**Seed protection:** The initial infected airport is excluded from closure in all strategies.

**Code:** `experiments.py` → `run_closure_budget_experiment()`, `closures.py` → `select_closed_nodes()`, `remove_closed_nodes()`

### Step 6: Measurements

For every simulation, we record:

| Metric | What it means |
|--------|---------------|
| **Final outbreak size** | Cumulative recovered fraction at end (total fraction ever infected) |
| **Peak infected fraction** | Maximum fraction infected at one time (health system pressure) |
| **Time to peak** | When maximum infection occurs |
| **LCC fraction** | Fraction of remaining airports in largest connected component (network damage) |

**Containment criterion:** Final outbreak size ≤ **5%**

**Code:** `metrics.py` → `epidemic_metrics()`, `resilience_metrics()`

### Step 7: Results (Main Finding at 20% Budget)

| Strategy | Final outbreak | Peak infected | LCC fraction |
|----------|---------------|---------------|--------------|
| Random | 61.63% | 25.45% | 91.55% |
| Degree | 3.00% | 0.80% | 4.04% |
| Closeness | 1.80% | 0.59% | 7.57% |
| Betweenness | 10.11% | 3.22% | 16.24% |
| Eigenvector | 6.43% | 2.22% | 12.12% |

**What these numbers mean:**

- **Random closure barely works** — even at 20% budget, 61.63% eventually infected. Random removal misses the airports that matter most.
- **Targeted closure works much better** — closeness gives 1.80%, degree gives 3.00%.
- **Trade-off:** Targeted strategies fragment the network. Degree leaves only 4.04% of remaining airports in the largest component — most surviving airports are in small disconnected pieces.

**Containment (≤5% final outbreak):**
- Degree reaches containment first at **18%**
- Closeness reaches it at **20%**
- Betweenness, eigenvector, random do not reach containment within 20%

**Code:** `results/openflights_closure_results_full.csv`, `results/openflights_closure_results_full.png`

### Step 8: Extra Experiments

#### A. Syntitive Networks (ER, BA, WS)

Tested on synthetic networks to check if results generalize beyond OpenFlights:
- **ER** (Erdős-Rényi): random connectivity
- **BA** (Barabási-Albert): hub-dominated
- **WS** (Watts-Strogatz): small-world structure

Purpose: implementation check + showing network structure affects spreading. Not used for main conclusion (short-horizon runs).

**Code:** `experiments.py` → `run_synthetic_network_comparison()`, `synthetic.py`

#### B. Degree-Preserving Null Model

Created a randomized version of OpenFlights that keeps the same degree sequence but changes detailed connections.

**Result at 10% degree removal:**
- Real graph: 29.3% LCC remaining
- Randomized graph: 61.5% LCC remaining

**Meaning:** Detailed topology matters, not just the degree sequence. The real network's specific hub connections make it more fragile to targeted removal.

**Code:** `experiments.py` → `run_degree_preserving_comparison()`, `synthetic.py` → `degree_preserving_randomization()`

#### C. Delayed Intervention

10% betweenness closure at different times:

| Intervention time | Final outbreak | Peak infected |
|-------------------|---------------|---------------|
| Time 0 (immediate) | 18.83% | 6.30% |
| Time 20 | 54.15% | 23.21% |
| Time 40 | 57.02% | 24.44% |

**Meaning:** Timing matters immensely. Once infection spreads widely, later closure cannot undo early spread.

**Code:** `experiments.py` → `run_delayed_intervention_experiment()`

### Step 9: The Report

**File:** `report/main_final.tex` → compiled to `report/PON_v1_2.pdf` (3 pages, IEEEtran format)

**Structure:**
1. Abstract
2. Motivation / Problem Statement
3. Methodology (Network construction, Centrality, Related work, SIR threshold, Metapopulation model, Interventions & measurements)
4. Results and Key Findings (with figures and table)
5. Discussion / Analysis
6. Conclusion

**References:** 7 sources (OpenFlights data, Keeling & Eames 2005, Pastor-Satorras et al. 2015, NetworkX, NumPy, pandas, matplotlib)

---

## 4. KEY NUMBERS CHEAT SHEET (for Viva)

| Quantity | Value |
|----------|-------|
| Full graph airports | 3,214 |
| Full graph routes | 18,858 |
| Connected components | 7 |
| Largest component airports | 3,188 |
| Largest component routes | 18,833 |
| Average degree (LCC) | 11.81 |
| β (infection rate) | 0.30 |
| γ (recovery rate) | 0.10 |
| R₀ = β/γ | 3 (> 1) |
| Mobility rate μ | 0.02 |
| Time step dt | 0.1 |
| Duration | 80 |
| Population per airport | 1 (normalized) |
| Initial infected fraction | 1% |
| Seed airport | Fixed high-degree (protected) |
| Random seed | 2026 |
| Budgets tested | 1% to 20% (every integer) |
| Random trials per budget | 5 |
| Containment criterion | final outbreak ≤ 5% |
| Random closure @20% | 61.63% |
| Closeness closure @20% | 1.80% |
| Degree closure @20% | 3.00% |
| Degree containment at | 18% |
| Closeness containment at | 20% |
| Delayed (0 / 20 / 40) | 18.83% / 54.15% / 57.02% |
| Null model: real vs randomized LCC @10% degree | 29.3% / 61.5% |

---

## 5. LIVE VIVA QUESTIONS & ANSWERS

### Q1: What is your project in one sentence?

**A:** We model epidemic spread across the OpenFlights airport network and compare which airport-closure strategy controls an outbreak best under limited closure budgets.

### Q2: Why use an undirected network?

**A:** Real flights are directed and weighted (different traffic each direction, different passenger volumes). We used undirected, unweighted edges as a simplifying assumption to study structural connectivity. This is a stated limitation.

### Q3: What is R₀ and what does R₀=3 mean?

**A:** R₀ = βS₀/γ is the basic reproduction number. With β=0.30 and γ=0.10, R₀=3. It means each infected person infects 3 others on average at the start — the outbreak can grow. Below 1 it dies out; above 1 it spreads.

### Q4: Why does closeness perform best?

**A:** Closeness identifies airports with short average paths to all others. Closing them makes global spread less efficient because they are the airports that can reach the rest of the network fastest.

### Q5: Why does degree reach containment first (at 18%)?

**A:** High-degree airports have many direct connections. Closing them removes many immediate pathways for movement and infection — they are local hubs that the epidemic needs to spread locally.

### Q6: Why is betweenness not the best despite fragmenting the network?

**A:** Betweenness identifies shortest-path bridges. Removing bridges fragments the network (high connectivity cost), but a bridge is not always the most important location for SIR dynamics. Direct hubs (degree) and globally accessible airports (closeness) also matter for transmission.

### Q7: Why compare against random closure?

**A:** Random closure is a baseline. It shows whether network-aware targeting provides real benefit beyond removing the same number of airports arbitrarily.

### Q8: Why run five random trials?

**A:** Random closure varies by chance — one random selection could be unusually lucky or unlucky. Repeating five times makes the comparison less dependent on one sample.

### Q9: What is the biggest result?

**A:** At 20% closure, random closure leaves 61.63% final outbreak, while targeted strategies reduce it sharply — closeness gives 1.80% and degree gives 3.00%.

### Q10: What is the trade-off?

**A:** Targeted strategies reduce outbreaks more strongly but fragment the network more severely. Degree leaves only 4.04% of remaining airports in the largest connected component at 20%. Real policy must balance epidemic control against connectivity loss.

### Q11: What are the limitations?

**A:** Routes are unweighted; no real passenger populations; parameters are scenario values not disease-calibrated; no rerouting/adaptive behavior after closures; single data snapshot (Oct 2026).

### Q12: What does the mobility term do?

**A:** It allows infection to spread between airports. People (including infected people) move along routes, carrying their infection status. Without mobility (μ=0), each airport's epidemic would be isolated.

### Q13: Why is the seed airport protected from closure?

**A:** Fairness. If one strategy could close the initial infected airport, it would "win" simply because the infection never starts — not because the strategy is better.

---

## 6. CODE FILE WHAT-EACH-DOES

| File | Purpose |
|------|---------|
| `config.py` | `ModelConfig` — all simulation parameters + validation |
| `network.py` | Parse OpenFlights, clean graph, largest component, graph summary |
| `centrality.py` | Compute degree/closeness/betweenness/eigenvector; rank nodes |
| `closures.py` | Select airports to close (strategies + budget); remove closed nodes |
| `sir.py` | Mean-field SIR + metapopulation SIR with mobility coupling |
| `metrics.py` | Epidemic metrics + resilience metrics |
| `synthetic.py` | Generate ER/BA/WS networks; degree-preserving randomization |
| `experiments.py` | Run closure-budget sweep, delayed intervention, synthetic comparison, null model |
| `plotting.py` | Plot budget results; plot mean-field threshold curves |
| `cli.py` | Command-line entry point with all subcommands |
| `__init__.py` | Package exports |

---

## 7. HOW TO REPRODUCE

```bash
# Install
pip install -e ".[dev]"

# Run tests
pytest

# Smoke test (no raw data needed)
python -m epidemic_network.cli smoke-test

# Real network summary
python -m epidemic_network.cli openflights-summary

# Full main sweep (matches report)
python -m epidemic_network.cli openflights-experiment \
  --output results/openflights_closure_results_full.csv \
  --duration 80 --dt 0.1 --random-trials 5
python -m epidemic_network.cli plot-results \
  --output results/openflights_closure_results_full.csv

# Delayed intervention
python -m epidemic_network.cli delayed-experiment \
  --output results/delayed_intervention_results_full.csv
```

---

## 8. FINAL 30-SECOND ANSWER (to end a viva)

> Our project used a real global airport network and an SIR-based metapopulation model to compare airport-closure strategies under limited budgets. We found that targeted closures based on network centrality are far more effective than random closure. Degree achieved the 5% containment criterion first at 18%, while closeness achieved the smallest final outbreak at 20%. The key lesson is that network structure matters, but intervention effectiveness must be balanced against the loss of transport connectivity.

---

*This document covers the complete project from start to end. Read it section by section, then try explaining each section out loud without looking at the text — that's the best viva preparation.*