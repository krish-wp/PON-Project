# Project Explanation: From Data to Final Results

## 1. Project title

**Containing Epidemics on the Global Air-Transport Network: Budget, Centrality, and the Epidemic Threshold**

This project asks a practical, measurable question:

> If an epidemic spreads through airports, and we can close only a limited number of airports, which airports should we close first?

The project does **not** claim to predict a particular disease or make a real-world forecast. It is a controlled network-science simulation for comparing intervention strategies under the same assumptions, initial condition, and closure budget.

## 1.1 What is included in the submission?

- [`report/PON_v1_2.pdf`](report/PON_v1_2.pdf) is the compiled IEEE-style report.
- `report/main_final.tex` is the LaTeX source used for the submitted report (builds `report/PON_v1_2.pdf`).
- `src/epidemic_network/` contains the parser, graph construction, centrality calculations, SIR integrators, experiments, metrics, and plotting code.
- `data/raw/` contains the OpenFlights `airports.dat`, `routes.dat`, and `SOURCE.txt` snapshot (downloaded 27 October 2026).
- `data/processed/` contains the generated network summary and centrality rankings.
- `results/` contains the generated CSV files and figures used for the analysis.

## 1.2 Module-by-module breakdown of the code

Each file in `src/epidemic_network/` has one clear job:

| File | What it does |
|------|-------------|
| `config.py` | `ModelConfig` dataclass with all simulation parameters (beta, gamma, mobility rate, dt, duration, population, initial infected fraction) and validation. |
| `network.py` | Parses OpenFlights `airports.dat`/`routes.dat`, cleans the graph (removes invalid IDs, self-loops, duplicates, isolates), extracts the largest connected component, and computes graph summaries. |
| `centrality.py` | Computes degree, closeness, betweenness, and eigenvector centrality for every airport using NetworkX, and ranks nodes for closure selection. |
| `closures.py` | Selects which airports to close for a given budget and strategy (random, degree, closeness, betweenness, eigenvector), and removes closed nodes from the graph. |
| `sir.py` | Implements the mean-field SIR integrator and the network metapopulation SIR integrator with graph-diffusion mobility coupling and delayed intervention support. |
| `metrics.py` | Computes epidemic metrics (final outbreak size, peak infected fraction, time to peak) and resilience metrics (LCC fraction, connected components, average degree). |
| `synthetic.py` | Generates ER, BA, WS synthetic networks and degree-preserving randomized graphs for null-model comparisons. |
| `experiments.py` | Runs the closure-budget sweep, delayed-intervention experiment, synthetic-network comparison, and degree-preserving null-model comparison. Aggregates results. |
| `plotting.py` | Plots budget results (outbreak size + LCC vs budget) and mean-field threshold curves. |
| `cli.py` | Command-line entry point with subcommands: smoke-test, synthetic-experiment, openflights-summary, openflights-experiment, delayed-experiment, synthetic-comparison, null-model-comparison, mean-field-plot, plot-results. |
| `__init__.py` | Package exports. |

## 1.3 Key numbers cheat sheet (for viva)

| Quantity | Value |
|----------|-------|
| Full graph airports | 3,214 |
| Full graph routes | 18,858 |
| Connected components | 7 |
| Largest component airports | 3,188 |
| Largest component routes | 18,833 |
| Average degree (LCC) | 11.81 |
| Beta (infection rate) | 0.30 |
| Gamma (recovery rate) | 0.10 |
| R0 = beta/gamma | 3 (> 1, outbreak can grow) |
| Mobility rate | 0.02 |
| Time step dt | 0.1 |
| Duration | 80 |
| Initial infected fraction | 1% (one fixed high-degree seed, protected from closure) |
| Random seed | 2026 |
| Closure budgets tested | 1% to 20% |
| Random trials per budget | 5 |
| Containment criterion | final outbreak ≤ 5% |
| Random closure final outbreak @20% | 61.63% |
| Closeness final outbreak @20% | 1.80% |
| Degree final outbreak @20% | 3.00% |
| Degree reaches containment at | 18% |
| Closeness reaches containment at | 20% |
| Delayed intervention (immediate / 20 / 40) | 18.83% / 54.15% / 57.02% |
| Degree-preserving null: real vs randomized LCC @10% degree removal | 29.3% / 61.5% |

---

## 2. Why did we choose this topic?

Airports connect cities across the world. If infected people travel, an infection can move from one region to another very quickly. Closing every airport is unrealistic because it would stop travel, trade, and essential movement. Therefore, the useful question is not "should we close all airports?" but:

> With a limited closure budget, how can we choose the most important airports?

This is a network problem because airports and routes form a connected graph.

---

## 3. What did we do overall?

We completed these steps:

1. Obtained real airport and route data from OpenFlights.
2. Converted the data into a network (graph).
3. Cleaned the network and selected its largest connected part.
4. Computed centrality scores for all airports.
5. Created an SIR epidemic model and a network version with movement across routes.
6. Closed airports using different strategies and budgets.
7. Compared the resulting epidemic size and network damage.
8. Ran additional checks: epidemic threshold, synthetic networks, a degree-preserving null model, and delayed intervention.
9. Wrote the results in an IEEE two-column report and checked the compiled PDF page count.

The main closure experiment is reproducible from the recorded defaults: seed `2026`, budgets `0.01` through `0.20`, five random trials, duration `80`, and time step `0.1`.

---

## 4. Step 1 - Getting the data

### What did we use?

We used the public **OpenFlights** dataset. It provides airport records and route records.

### How did we represent it?

- An **airport** became a network node.
- A **route** between two airports became an edge.

For this course project, we treated routes as **undirected**. In other words, if there is a route between airport A and airport B, we assume movement can happen in both directions.

### Why did we simplify it this way?

Real airline travel is directed and weighted: A to B may have different traffic from B to A, and some routes carry far more passengers. We used an undirected, unweighted network so that we could focus on the main network-structure question. This is an important limitation, not a claim that real flights work exactly this way.

---

## 5. Step 2 - Cleaning and building the network

### What did we clean?

We removed:

- invalid airport or route identifiers,
- self-loops (an airport connected to itself),
- duplicate routes,
- isolated airports that have no useful route connection.

### What network did we obtain?

The cleaned full graph had:

- 3,214 airports,
- 18,858 routes,
- 7 connected components.

The largest connected component had:

- 3,188 airports,
- 18,833 routes,
- average degree about 11.81.

### Why use the largest connected component?

An epidemic can spread through routes only inside a connected component. The largest component contains almost all the airports, so it is the meaningful part of the network for one global spreading experiment.

---

## 6. Step 3 - Understanding centrality

Centrality measures tell us which airports are structurally important. We used four measures.

### Degree centrality

An airport with high degree has many direct route connections.

**Idea:** Closing a high-degree airport removes a strong local travel hub.

### Closeness centrality

An airport with high closeness has short average path distance to the rest of the network.

**Idea:** Closing it can reduce fast access across the network.

### Betweenness centrality

An airport with high betweenness lies on many shortest paths between other airports.

**Idea:** It can act like a bridge between regions.

### Eigenvector centrality

An airport has high eigenvector centrality if it is connected to other important airports.

**Idea:** It identifies airports influential through their neighbours as well as their own direct links.

### Why use several centralities?

There is no single universal meaning of "important" in a network. A local hub, a global shortcut, and a bridge can all be important in different ways. Comparing strategies lets the data show which type of importance matters most for this epidemic model.

---

## 7. Step 4 - The epidemic model

### The basic SIR model

At each airport, the population is divided into three compartments:

- **S - Susceptible:** can become infected.
- **I - Infected:** currently infectious.
- **R - Recovered:** no longer infectious.

The basic equations are:

```text
dS/dt = -beta * S * I
dI/dt =  beta * S * I - gamma * I
dR/dt =  gamma * I
```

Here:

- `beta` is the infection/transmission rate.
- `gamma` is the recovery rate.

We used beta = 0.30 and gamma = 0.10.

### Epidemic threshold

The mean-field threshold is:

```text
R0 = beta * S0 / gamma
```

If R0 is above 1, infection can initially grow. If it is below 1, it tends to die out. In our starting situation, R0 is above 1 (R0 = 3), so an outbreak can grow. We plotted below-threshold, threshold, and above-threshold behaviour to validate this basic theory.

### Network metapopulation model

The simple SIR model describes one population. Our main model applies an SIR system at every airport. It also adds a graph-diffusion term, which allows susceptible, infected, and recovered populations to move through connected routes.

So infection spreads in two ways:

1. **Local transmission:** infection grows within an airport.
2. **Network movement:** people, including infected people, move along flight routes.

### How did we simulate it?

We used the Euler numerical method. At every small time step, it calculates the change in S, I, and R, then updates the values.

Main parameters for the real-network closure sweep:

- beta = 0.30,
- gamma = 0.10,
- mobility rate = 0.02,
- time step `dt` = 0.1,
- total duration = 80,
- normalized population = 1 per airport,
- initial infected fraction = 1% at one airport,
- random seed = 2026 for random closure selection.

The compact synthetic and delayed-intervention commands use shorter runs and may use different time steps; those settings are described separately below. They must not be confused with the parameters of the main 1--20% sweep.

---

## 8. Step 5 - Airport closure experiment

### What was the experiment?

For each strategy, we closed a selected fraction of airports. We tested every budget from 1% to 20%.

Strategies:

1. Random closure
2. Degree-based closure
3. Closeness-based closure
4. Betweenness-based closure
5. Eigenvector-based closure

For a centrality strategy, we closed the airports with the highest score. For random closure, we selected the same number of airports randomly. The number of closed airports is `ceil(budget × number of airports)`, with at least one airport selected for a positive budget. We repeated random closure five times because a single random selection could be unusually lucky or unlucky.

### Important fairness rule

Every strategy must start with the same initial infection. We selected one fixed high-degree seed airport and **protected it from closure**.

Why is this important? If one strategy is allowed to close the initial infected airport, it could appear successful simply because the infection never starts. That would make the comparison unfair.

---

## 9. Step 6 - What did we measure?

For every simulation, we recorded:

### Final outbreak size

This is the final recovered fraction divided by the final total population. In an SIR model, recovered people represent everyone who was infected and then left the infectious state. Therefore, it estimates the cumulative fraction affected by the epidemic. It is not the fraction infected at the final time.

### Peak infected fraction

This is the largest fraction infected at the same time. It represents pressure on health systems.

### Time to peak

This is when the maximum infection level occurs.

### Largest connected component (LCC) fraction

This shows the fraction of the remaining airports contained in the largest connected component after closures. It is a structural connectivity measure, not a passenger-flow measure.

### Why measure both outbreak and connectivity?

An intervention can reduce infection by breaking the transport network apart. That may be effective for health, but it also damages travel connectivity. A good analysis should show both the benefit and the cost.

---

## 10. Main results

### At 20% closure budget

| Strategy | Final outbreak | Peak infected | LCC fraction |
|---|---:|---:|---:|
| Random | 61.63% | 25.45% | 91.55% |
| Degree | 3.00% | 0.80% | 4.04% |
| Closeness | 1.80% | 0.59% | 7.57% |
| Betweenness | 10.11% | 3.22% | 16.24% |
| Eigenvector | 6.43% | 2.22% | 12.12% |

### How should we explain this result?

- Random closure barely controls the epidemic, even when 20% of airports are removed.
- Targeted closure is much more effective because it removes structurally important airports.
- Closeness gives the smallest final outbreak at the 20% budget.
- Degree reaches the containment criterion first: it reduces final outbreak size to 5% or less at 18% closure.
- Targeted strategies also cause severe network fragmentation. For example, degree closure leaves only about 4.04% of remaining airports in the largest connected component at 20% closure.

### Containment criterion

We defined containment as final outbreak size at most 5%.

- Degree reaches containment at 18% closure.
- Closeness reaches containment at 20% closure.
- Betweenness, eigenvector, and random closure do not reach containment within 20%.

### Main conclusion from the result

Targeted interventions are far better than random interventions. However, the strategy that best reduces the epidemic is not always the strategy that best preserves connectivity. Policy decisions should consider both objectives.

---

## 11. Extra experiments and why we included them

### A. Synthetic ER, BA, and WS networks

We compared the framework on ER, BA, and WS networks.

- ER: more random connectivity.
- BA: hub-dominated network.
- WS: small-world structure.

**Why?** This checks that the approach works beyond one dataset and shows that network structure affects epidemic spreading. These runs are short implementation checks, not replacements for the main OpenFlights experiment.

### B. Degree-preserving randomized network

We created a randomized version of the OpenFlights graph that keeps the same degree sequence but changes detailed connections.

**Why?** If results depended only on degree, the real and randomized networks would behave similarly. The difference under degree-based removal shows that detailed topology matters, not only how many links each airport has.

### C. Delayed intervention

We used 10% betweenness closure at intervention times 0, 20, and 40 time units.

- Immediate intervention: 18.83% final outbreak.
- Intervention at time 20: 54.15% final outbreak.
- Intervention at time 40: 57.02% final outbreak.

**Why?** It demonstrates that timing matters. Once infection has already spread widely, later closure cannot undo early spread.

---

## 12. Limitations - say these honestly in a viva

1. Routes are undirected and unweighted.
2. All airport populations are normalized instead of using real passenger populations.
3. Beta, gamma, and mobility are scenario parameters, not calibrated to one real disease.
4. The model does not include rerouting, passenger behaviour, vaccination, or changing travel schedules.
5. Airport closure may be economically and socially costly; we measure connectivity loss but not full economic cost.

These limitations do not make the project invalid. They define what the model can and cannot claim, and they prevent the results from being overinterpreted as operational policy recommendations.

---

## 13. Future improvements

If we had more time, we would:

- use directed, weighted routes and passenger volumes,
- use realistic airport populations,
- calibrate model parameters using a particular disease,
- compare airport closure with vaccination, testing, screening, or travel reduction,
- optimize both epidemic reduction and connectivity/economic cost together,
- report uncertainty intervals for every strategy.

---

## 14. How to reproduce the project

From the project root, install the package and development dependencies:

```powershell
python -m pip install -e ".[dev]"
```

Run the tests:

```powershell
python -m pytest
```

Run the fast smoke test without the raw OpenFlights files:

```powershell
python -m epidemic_network.cli smoke-test
```

After placing `airports.dat` and `routes.dat` in `data/raw/`, generate the processed network information:

```powershell
python -m epidemic_network.cli openflights-summary
```

Run the full main sweep and plot:

```powershell
python -m epidemic_network.cli openflights-experiment `
  --output results/openflights_closure_results_full.csv `
  --duration 80 --dt 0.1 --random-trials 5
python -m epidemic_network.cli plot-results `
  --output results/openflights_closure_results_full.csv
```

The commands use the default 1--20% budgets and fixed seed `2026`. Results should be regenerated rather than manually edited. The report values are rounded summaries of the generated CSV files.

---

## 15. Short answers for common viva questions

### Why did you use random closure?

It is a baseline. It tells us whether network-aware targeting is actually better than removing the same number of airports arbitrarily.

### Why did you use five random trials?

Random results change with the sampled airports. Repeating it five times reduces the effect of one unusual random sample.

### Why is betweenness not the best strategy here?

Betweenness identifies shortest-path bridges. Removing bridges fragments the network, but a bridge is not always the most important location for the SIR dynamics. Direct hubs and global accessibility also matter.

### Why does degree perform well?

High-degree airports have many direct connections. Closing them removes many immediate pathways for movement and infection.

### Why does closeness perform well?

High-closeness airports can reach the rest of the network through short paths. Removing them makes global spread less efficient.

### What is the biggest result?

At 20% closure, random removal leaves a final outbreak around 61.63%, while targeted strategies reduce it sharply. Closeness gives 1.80% and degree gives 3.00%.

### What is the final conclusion?

With a limited closure budget, targeted centrality-based airport closure is much more effective than random closure. But strong epidemic control comes with a large connectivity cost, so real policy should balance both.

---

## 16. Final 30-second answer to end a viva

Our project used a real global airport network and an SIR-based metapopulation model to compare airport-closure strategies under limited budgets. We found that targeted closures based on network centrality are far more effective than random closure. Degree achieved the 5% containment criterion first at 18%, while closeness achieved the smallest final outbreak at 20%. The key lesson is that network structure matters, but intervention effectiveness must be balanced against the loss of transport connectivity.
