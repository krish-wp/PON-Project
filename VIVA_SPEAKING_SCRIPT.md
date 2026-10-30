# VIVA SPEAKING SCRIPT — Complete Start-to-End Narrative

**Instructions:** Read this aloud 3–4 times until you can say it naturally. Do not memorize word-for-word; memorize the **flow** and the **~12 key numbers**. Speak continuously. If the examiner tries to interrupt, say *"Just one second, I'll cover that in a moment"* and keep going.

---

## PART 1: INTRODUCTION (30 seconds)

"Good morning/afternoon. I am [Your Name], part of Group 22. Our project is titled **'Containing Epidemics on the Global Air-Transport Network: Budget, Centrality, and the Epidemic Threshold.'**

In one sentence: we modeled how epidemics spread through the real global airport network, and we tested which airports to close—under a limited budget—to control an outbreak most effectively.

Air travel connects distant populations and can accelerate geographic epidemic spread. When an outbreak starts, closing every airport is not realistic—it would stop trade, essential travel, and emergency movement. So the practical question is not whether to close airports, but **which** airports to close given a limited budget. That is exactly what this project answers."

---

## PART 2: DATA AND NETWORK (1 minute)

"We used the public **OpenFlights** dataset, downloaded on 27 October 2026. It provides airport records and route records.

In our network, **airports became nodes** and **routes became undirected edges**—meaning if a route exists between airport A and airport B, we assumed people can travel in both directions.

We cleaned the data: we removed invalid numeric identifiers, self-loops (an airport connected to itself), duplicate routes, and isolated airports that have no connections.

The cleaned full graph had **3,214 airports** and **18,858 routes** in **7 connected components**. Its largest component had **3,188 airports**, **18,833 routes**, and an **average degree of 11.81**.

We ran our epidemic experiments on this **largest connected component** because an epidemic can only spread inside a connected part of the network. The other components are tiny and disconnected, so they do not matter for one global spreading experiment."

---

## PART 3: CENTRALITY MEASURES (45 seconds)

"We computed four centrality measures for every airport using NetworkX:

- **Degree centrality** — counts direct connections. Closing a high-degree airport removes a strong local travel hub.
- **Closeness centrality** — measures average distance to all other airports. Closing it reduces fast access across the network.
- **Betweenness centrality** — counts shortest paths passing through an airport. It acts like a bridge between regions.
- **Eigenvector centrality** — rewards connections to other important airports. It identifies airports influential through their neighbours as well as their own direct links.

For a budget *b*, we closed the top ⌈b×|V|⌉ airports for each centrality strategy. Random closure sampled the same number of airports using a fixed seed, so it serves as a fair baseline."

**Top airports (drop this if you want to impress):**
- Degree: Schiphol (580), Frankfurt (340), Charles de Gaulle (1382)
- Closeness: Frankfurt (340), Charles de Gaulle (1382), Heathrow (507)
- Betweenness: Charles de Gaulle (1382), LAX (3484), Anchorage (3774)
- Eigenvector: Schiphol (580), Frankfurt (340), Charles de Gaulle (1382)

---

## PART 4: EPIDEMIC MODEL (1 minute)

"The basic model is **SIR**—Susceptible, Infected, Recovered.

- **S** = Susceptible: can become infected
- **I** = Infected: currently infectious  
- **R** = Recovered: no longer infectious

The equations are:
- dS/dt = −βSI
- dI/dt = βSI − γI
- dR/dt = γI

Where **β = 0.30** is the infection rate and **γ = 0.10** is the recovery rate.

The key quantity is **R₀ = βS₀/γ**. If R₀ is below 1, the outbreak dies out. If R₀ is above 1, the outbreak can grow. With β = 0.30 and γ = 0.10, we get **R₀ = 3**, which is greater than 1—so under our assumptions, an outbreak can spread. This is the epidemic threshold we validate.

**But our model goes further:** we used a **network metapopulation model**. Instead of one population, we ran an SIR system at *every* airport and let people move between connected airports.

Each airport has its own S, I, and R populations. Infection spreads locally at rate βSᵢIᵢ/Nᵢ. People recover at rate γIᵢ. And a graph-diffusion term couples neighbouring airports: for each compartment, mobility adds μ(ΣXⱼ − kᵢXᵢ), where kᵢ is airport i's degree. In plain terms: people leave airport i and arrive at its neighbours, carrying their infection status with them.

So infection spreads in **two ways**:
1. **Local transmission** within an airport
2. **Network movement**—infected people travel along flight routes"

---

## PART 5: SIMULATION PARAMETERS (45 seconds)

"We integrated the model using the explicit **Euler method**. Our parameters were:

- β = 0.30 (infection rate)
- γ = 0.10 (recovery rate)
- Mobility rate = 0.02
- Normalized population = 1 per airport
- dt = 0.1 (time step)
- Duration = 80 time units

The initial infected fraction was **1% at one fixed high-degree seed airport**. We **protected this seed airport from closure** so that every strategy is evaluated from the same initial condition. This is a fairness rule—otherwise, a strategy could 'win' simply by closing the airport where the infection starts.

For **immediate closure**, we removed the selected airports and their routes before simulation started. For **delayed closure**, we removed mobility edges to closed airports and set local infection to zero at the intervention time, while existing populations remained and could recover."

---

## PART 6: CLOSURE EXPERIMENT (1 minute)

"We compared **five strategies** for budgets from **1% to 20%**:

1. **Random closure** — baseline, same number of airports chosen randomly
2. **Degree-based closure** — highest degree centrality first
3. **Closeness-based closure** — highest closeness centrality first
4. **Betweenness-based closure** — highest betweenness centrality first
5. **Eigenvector-based closure** — highest eigenvector centrality first

The number of closed airports is ⌈budget × number of airports⌉, with at least one airport selected for a positive budget.

We repeated random closure **five times** because a single random draw could be unusually lucky or unlucky. Centrality strategies are deterministic, so one trial each.

For every simulation, we recorded:
- **Final outbreak size** — cumulative recovered fraction at the end
- **Peak infected fraction** — largest fraction infected at one time (health system pressure)
- **Time to peak** — when maximum infection occurs
- **Largest connected component fraction** — how much of the remaining network stays connected

We defined **containment** as final outbreak size at most **5%**."

---

## PART 7: MAIN RESULTS (1 minute)

"Here are the headline results at a **20% budget**:

| Strategy | Final Outbreak | Peak Infected | LCC Fraction |
|----------|---------------|---------------|--------------|
| Random | 61.63% | 25.45% | 91.55% |
| Degree | 3.00% | 0.80% | 4.04% |
| Closeness | 1.80% | 0.59% | 7.57% |
| Betweenness | 10.11% | 3.22% | 16.24% |
| Eigenvector | 6.43% | 2.22% | 12.12% |

**What this means:**

**Random closure barely works.** Even at a 20% budget, it leaves 61.63% of the population eventually infected. Random removal misses many of the airports that matter most for transmission.

**Targeted closure works much better.** Closeness gives only **1.80%** final outbreak, and degree gives **3.00%**. Targeted strategies remove structurally important airports—hubs with many connections, or airports that lie on many shortest paths—so they block far more transmission paths per closed airport.

**Degree reached containment first at 18%.** Closeness reached containment at 20%. Betweenness, eigenvector, and random closure did not reach containment within the tested range.

**The trade-off is connectivity.** Targeted strategies fragment the network more severely. Degree closure leaves only **4.04%** of remaining airports in the largest connected component at 20%, meaning most surviving airports are in small, disconnected pieces."

---

## PART 8: EXTRA EXPERIMENTS (45 seconds)

"We ran three supporting experiments.

**Synthetic networks:** We tested ER, BA, and WS networks at a 10% budget. These were short-horizon implementation checks, not used for the main conclusion.

**Degree-preserving null model:** We randomized the OpenFlights graph while keeping the same degree sequence. Under degree removal, the real graph dropped to 29.3% largest-component fraction, while the randomized graph stayed at 61.5%. This shows **detailed topology matters**, not just how many links each airport has.

**Delayed intervention:** With a fixed 10% betweenness closure budget:
- Immediate intervention: 18.83% final outbreak
- Intervention at time 20: 54.15%
- Intervention at time 40: 57.02%

This demonstrates that **timing matters**. Once infection has spread widely, later closure cannot undo the early spread."

---

## PART 9: DISCUSSION AND LIMITATIONS (45 seconds)

"The real network is heterogeneous—a small set of airports has a large role in connecting otherwise weakly connected regions. Degree and closeness performed best for reducing the cumulative outbreak. Betweenness caused strong fragmentation but did not achieve containment by 20%.

Anchorage ranks third on betweenness because many intercontinental shortest paths pass through high-latitude connections, yet it is not the most valuable target for suppressing transmission. Structural importance for connectivity and epidemic suppression need not be identical.

The appropriate strategy depends on whether the objective prioritizes epidemic reduction, connectivity preservation, or a weighted combination of both. A real health authority would need to balance lives saved against the economic and social cost of disconnecting cities.

**Limitations:** OpenFlights route records do not provide passenger populations or time-varying traffic, so we used normalized airport populations and unweighted routes. The SIR parameters are scenario parameters rather than estimates for a particular disease. Finally, we did not model rerouting or behavioral adaptation—for example, if an airport closes, travelers may find alternative routes, which our model does not capture."

---

## PART 10: CONCLUSION (30 seconds)

"This project provides a reproducible framework for comparing airport closure strategies on a real flight network.

The mean-field model validates the epidemic threshold—R₀ = 3 > 1 under our parameters—so an outbreak can grow.

The metapopulation model connects local SIR dynamics to global network structure.

**Degree reached the 5% containment criterion first, at 18% closure, while closeness produced the smallest final outbreak at 20% (1.80%).** Both achieved this by strongly fragmenting the network.

So the final lesson is: **effective control must be balanced against connectivity loss.**"

---

## KEY NUMBERS CHEAT SHEET (Drop these naturally)

If the examiner asks anything, just state these numbers:

| Quantity | Value |
|----------|-------|
| Full graph airports / routes | 3,214 / 18,858 |
| Connected components | 7 |
| Largest component airports / routes | 3,188 / 18,833 |
| Average degree | 11.81 |
| β (infection rate) | 0.30 |
| γ (recovery rate) | 0.10 |
| R₀ = β/γ | 3 (> 1) |
| Mobility rate μ | 0.02 |
| Time step dt | 0.1 |
| Duration | 80 |
| Initial infected fraction | 1% |
| Random seed | 2026 |
| Random @20% final outbreak | 61.63% |
| Closeness @20% | 1.80% |
| Degree @20% | 3.00% |
| Degree containment at | 18% |
| Delayed (0 / 20 / 40 units) | 18.83% / 54.15% / 57.02% |

---

## HOW TO USE THIS SCRIPT

1. **Read it aloud** 3–4 times until it flows naturally.
2. **Don't memorize word-for-word.** Memorize the flow and the key numbers table.
3. **If the examiner interrupts:** Smile, say *"That's a great point—let me finish this section and I'll address it,"* then continue for 10 more seconds before answering.
4. **If they ask a question you didn't cover:** Say *"That's covered in our limitations section—we acknowledge that..."* and pivot back to what you know.
5. **End with the 30-second conclusion** and stop talking. Let them ask questions then.

You've built this. You know it. Speak with confidence."
