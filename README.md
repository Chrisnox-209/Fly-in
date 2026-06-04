# ✈️ Fly-In — Drone Traffic Simulator

*This project has been created as part of the 42 curriculum by cpietrza.*

==GIF_MENU==

---

## 📋 Table of Contents

- [Description](#-description)
- [Algorithm & Implementation](#-algorithm--implementation)
- [Visual Representation](#-visual-representation)
- [Project Structure](#-project-structure)
- [Map Format](#-map-format)
- [Drone Fleet](#-drone-fleet)
- [Keyboard Shortcuts](#-keyboard-shortcuts)
- [Installation & Execution](#-installation--execution)
- [Makefile Commands](#-makefile-commands)
- [Available Maps](#-available-maps)
- [Resources](#-resources)

---

## 📖 Description

**Fly-In** is a drone traffic simulation tool built as part of the 42 curriculum. The goal is to route a fleet of drones from a **start hub** to an **end hub** through a network of interconnected hubs and connections, while respecting capacity constraints at every step.

The simulator automatically solves the routing problem and plays a real-time visual animation of all drone movements, including collisions avoidance, zone constraints, and congestion management.

### Key Features

- 🗺️ **Custom map format** — define your own hub networks in simple `.txt` files
- 🤖 **Automatic solver** — A* pathfinding with time-expanded state space
- 🎮 **Interactive visualizer** — real-time Pygame rendering with zoom, pan, and speed control
- 🚫 **Zone types** — Normal, Priority, Restricted, and Blocked zones with different traversal costs
- 📊 **Simulation output** — step-by-step console output in standardized format (VII.5)
- ✅ **Map validation** — full Pydantic validation with helpful error messages for invalid maps

---

## 🧠 Algorithm & Implementation

### Pathfinding: Time-Expanded A\*

The core of Fly-In is a **time-expanded A\*** algorithm implemented in [`solver.py`](solver.py).

---

#### 🔷 The Problem

Routing a single drone on a graph is trivial. The challenge here is routing **N drones simultaneously** while ensuring that:
- No hub ever exceeds its `max_drones` capacity at any given turn
- No connection ever exceeds its `max_link_capacity` at any given turn
- No two drones collide or deadlock

This turns a simple shortest-path problem into a **multi-agent time-constrained routing problem**.

---

#### 🔷 State Space: The Time Dimension

A standard A* operates on nodes: `state = hub`. It cannot reason about *when* a drone is somewhere.

The time-expanded A* extends the state with a time dimension:

```
state = (hub_name, turn)
```

- **Initial state**: `(start_hub, 0)`  
- **Goal**: any state `(end_hub, T)` for any turn `T`

This means the graph explored is not the original map graph but a **layered copy** of it — one layer per turn — where edges connect `(hub, t)` to `(neighbor, t + cost)`.

---

#### 🔷 Zone Costs

Each hub has a zone type that defines how many turns a drone must spend traversing it:

| Zone       | Symbol | Cost `c` | Meaning                            |
|------------|--------|----------|------------------------------------|
| Normal     | —      | `1`      | Standard traversal                 |
| Priority   | `P`    | `1`      | Fast lane, standard cost           |
| Restricted | `!`    | `2`      | Requires 2 turns to pass through   |
| Blocked    | `X`    | `∞`      | Cannot be entered — skipped        |

When a drone moves from hub `A` to hub `B` with zone cost `c`, the transition is:

```
(A, t)  ──►  (B, t + c)
```

If a drone **waits** at its current hub instead of moving:

```
(A, t)  ──►  (A, t + 1)   [wait penalty: +1e-6 to deprioritize waiting]
```

---

#### 🔷 The A\* Score Formula

For each candidate next state `(next_hub, end_turn)`, the total score used by A* is:

```
f(s) = g(s) + h(s)
```

Where:

```
g(s) = accumulated cost so far
     = g(parent) + zone_cost(next_hub) + wait_penalty + backtrack_penalty

h(s) = heuristic: estimated minimum cost from next_hub to end_hub
     = distance_to_end[next_hub]   (precomputed by Dijkstra)
```

**Penalties applied to `g`:**

| Penalty              | Value   | Applied when                                          |
|----------------------|---------|-------------------------------------------------------|
| `wait_penalty`       | `1e-6`  | Drone stays at the same hub (waiting)                 |
| `backtrack_penalty`  | `2.0`   | `h(next_hub) > h(current_hub)` — moving away from goal|

The backtrack penalty discourages the solver from exploring paths that move further from the goal without a good reason.

---

#### 🔷 Heuristic: Backward Dijkstra

Before routing any drone, the solver runs a **Dijkstra from the end hub** backwards through the graph to compute the minimum cost from every reachable hub to the goal:

```
distance_to_end[hub] = min cost to reach end_hub from hub
```

This gives an **admissible heuristic** (never overestimates) because it uses actual zone costs on the real graph — making A* both complete and optimal.

---

#### 🔷 Capacity Constraints

Two logs track occupancy across time:

```python
flight_log[(hub, turn)]          → number of drones at hub at that turn
link_log[(hub_a, hub_b, turn)]   → number of drones on link A-B at that turn
```

Before adding `(next_hub, end_turn)` to the open set, the solver checks:

```
for t in [current_turn+1 .. end_turn]:
    if flight_log[(next_hub, t)] >= max_drones(next_hub): BLOCKED

for t in [current_turn .. end_turn-1]:
    if link_log[(current_hub, next_hub, t)] >= max_link_capacity: BLOCKED
```

This ensures **no over-capacity state is ever explored**.

---

#### 🔷 Sequential Multi-Drone Routing

Drones are planned **one at a time** in order `D0, D1, D2, ...`.

After each drone's path is found, its occupancy is **committed** to `flight_log` and `link_log`. The next drone then plans around all previously committed drones.

This greedy sequential approach has complexity `O(N × A*)` instead of the exponential `O(A*^N)` of joint planning, while still finding valid (often optimal) solutions in practice.

---

#### 🔷 Waypoints

For each connection `A–B`, a virtual **waypoint** node `wp_A_B` is generated at the midpoint:

```
A  ──►  wp_A_B  ──►  B
```

Waypoints serve two purposes:
1. **Visual**: drones animate smoothly mid-flight on connections
2. **Logical**: the solver can distinguish drones *in transit* from drones *at a hub*, allowing more precise capacity tracking

---

#### 🔷 Safety Limit & Error Handling

- If a drone's A* search exceeds **turn 2000**, it returns `None` → `ValueError` is raised
- Maps with blocked paths or insufficient capacity to route any drone also raise `ValueError`
- The UI catches these errors and displays a readable message instead of crashing

---

## 🎨 Visual Representation

The visualizer (`generator_map.py` + `game.py`) uses **Pygame** to provide a rich interactive simulation.

### Hub Rendering

Each hub is drawn as a colored circle. Its radius scales with its `max_drones` capacity — larger hubs are visually bigger. Zone badges are displayed in the center of the hub:

| Zone       | Badge | Ring color             |
|------------|-------|------------------------|
| Normal     | —     | Hub's assigned color   |
| Priority   | `P`   | Blue outer ring        |
| Restricted | `!`   | Orange outer ring      |
| Blocked    | `X`   | Red outer ring         |

### Drone Animation

Drones are animated sprites that interpolate smoothly between hubs. Each drone is randomly assigned one of five color variants. They rotate to face their destination and their propellers spin faster while in motion. During inter-turn pauses, drones hover in place with slow propeller rotation and the background parallax also freezes.

### Connections

Connections are drawn as lines between hubs. A small badge in the middle shows the link's capacity (`max_link_capacity`). The line thickness increases for higher-capacity links.

### Tooltip (Hover Info)

Hovering over any hub or connection shows a real-time tooltip:
- **Hub tooltip**: hub name, current drone count vs capacity, list of drone IDs present
- **Connection tooltip**: connection name, current transit count vs capacity, drone IDs in transit
- Drones that have **finished** at the end hub are also tracked and shown in the tooltip

### Background Parallax

A multi-layer cloud parallax animation plays in the background. It is synchronized with drone movement — it scrolls only during the movement phase of each turn and pauses during inter-turn gaps, exactly matching the drone animation cycle.

### Legend Panel

A persistent legend is displayed in the top-right corner showing:
- Keyboard shortcuts with live state (e.g., `W: Background (ON)`)
- Hub zone types with their color indicator and cost description

### End Screen

When all drones reach the goal, a popup displays:
- Map name
- Total drones
- Total turns taken

---

## 📁 Project Structure

```
Fly-In/
├── fly-in.py              # Entry point
├── game.py                # Main game loop, camera, UI, tooltip, legend
├── generator_map.py       # Pygame sprites: VisualNode, VisualDrone, GraphRenderer
├── solver.py              # A* traffic controller & pathfinding
├── parser.py              # Map file parser & Pydantic validation
├── structure.py           # Data structures: Node, Hub, Start, End, Connection, Drone
├── menu.py                # Main menu, map selector, animated buttons
├── convertisseur.py       # GIF-to-Pygame frame converter
├── Makefile               # Build, lint, run commands
├── pyproject.toml         # Python dependencies (uv)
├── .flake8                # Flake8 configuration (max-line-length = 120)
├── assets/                # Images, drone sprites, GIFs, cloud backgrounds
└── maps/
    ├── easy/              # 3 beginner maps
    ├── medium/            # 3 intermediate maps
    ├── hard/              # 3 advanced maps
    ├── challenger/        # 1 extreme map
    └── custom/            # Custom & test maps (including error cases)
```

---

## 🗺️ Map Format

Maps are plain `.txt` files. Here is a complete example:

```
# My map title
nb_drones: 3

start_hub: start 0 0 [color=green max_drones=5]
hub: waypoint 1 0 [color=blue max_drones=2 zone=priority]
hub: danger  2 0 [color=red  zone=restricted]
end_hub: goal 3 0 [color=green max_drones=5]

connection: start-waypoint [max_link_capacity=2]
connection: waypoint-danger
connection: danger-goal
```

### Syntax Reference

| Keyword         | Description                                             |
|-----------------|---------------------------------------------------------|
| `nb_drones: N`  | Number of drones to route                               |
| `start_hub:`    | The unique departure zone                               |
| `end_hub:`      | The unique arrival zone                                 |
| `hub:`          | An intermediate zone                                    |
| `connection:`   | A bidirectional link between two hubs (`A-B`)           |

### Hub Options `[...]`

| Option                  | Default   | Description                          |
|-------------------------|-----------|--------------------------------------|
| `color=<name>`          | grey      | Display color                        |
| `max_drones=N`          | 1         | Max simultaneous drones in the hub   |
| `zone=normal`           | normal    | Zone type (see cost table above)     |

### Connection Options `[...]`

| Option                  | Default | Description                                |
|-------------------------|---------|--------------------------------------------|
| `max_link_capacity=N`   | 1       | Max simultaneous drones on the link        |

### Available Colors

`yellow` `grey` `red` `orange` `brown` `blue` `green` `pink` `cyan`
`purple` `lime` `magenta` `gold` `black` `maroon` `darkred` `violet`
`crimson` `rainbow`

---

## 🚁 Drone Fleet

Each drone is randomly assigned one of five visual models at the start of the simulation:

| Model  | Color | Preview |
|--------|-------|---|
| Blue   | 🔵 | <img src="assets/blue_drone.gif" width="60"> |
| Green  | 🟢 | <img src="assets/green_drone.gif" width="60"> |
| Red    | 🔴 | <img src="assets/red_drone.gif" width="60"> |
| Gold   | 🟡 | <img src="assets/gold_drone.gif" width="60"> |
| Yellow | 💛 | <img src="assets/yellow_drone.gif" width="60"> |

---

## ⌨️ Keyboard Shortcuts

These shortcuts are available during simulation and are also displayed in the **in-game legend panel** (top-right corner):

| Key               | Action                                      |
|-------------------|---------------------------------------------|
| `SPACE`           | Play / Pause the simulation                 |
| `→` Right Arrow   | Increase simulation speed (`×1` → `×2` → `×4` → `×8`) |
| `←` Left Arrow    | Decrease simulation speed (`×8` → `×4` → `×2` → `×1`) |
| `W`               | Toggle background parallax animation (ON/OFF) |
| Right Click + Drag| Pan / move the camera                       |
| Mouse Wheel       | Zoom in / Zoom out                          |

---

## 🎮 Simulation Demo

==GIF_DEMO==

---

## ⚙️ Installation & Execution

### Requirements

- Python **≥ 3.12**
- [`uv`](https://docs.astral.sh/uv/) — fast Python package manager

### Install uv

```bash
curl -Lsf https://astral.sh/uv/install.sh | sh
```

### Install dependencies

```bash
make install
```

### Run the simulator

```bash
make run
```

### Run linting checks
```bash
make lint
```

### Run strict linting checks
```bash
make lint-strict
```

### Run the application in debug mode
```bash
make debug
```

### Clean application files

```bash
make clean
```



---

## 🛠️ Makefile Commands

| Command           | Description                                                        |
|-------------------|--------------------------------------------------------------------|
| `make install`    | Install all Python dependencies via `uv sync`                      |
| `make run`        | Launch the simulator                                               |
| `make lint`       | Run `mypy` (type checking) + `flake8` (style)                      |
| `make lint-strict`| Run `mypy --strict` + `flake8` (stricter type checking)            |
| `make debug`      | Launch the simulator under `pdb` debugger                          |
| `make clean`      | Remove `.venv`, `__pycache__`, `.mypy_cache`, `uv.lock`            |

---

## 🗂️ Available Maps

### 🟢 Easy

| File                  | Description                              |
|-----------------------|------------------------------------------|
| `01_linear_path.txt`  | Simple straight line, no constraints     |
| `02_simple_fork.txt`  | First fork to choose a path              |
| `03_basic_capacity.txt` | Introduction to capacity limits        |

### 🟡 Medium

| File                    | Description                               |
|-------------------------|-------------------------------------------|
| `01_dead_end_trap.txt`  | Dead-end that can lure drones off course  |
| `02_circular_loop.txt`  | Loop structure requiring careful planning |
| `03_priority_puzzle.txt`| Mix of zone types and capacity limits     |

### 🔴 Hard

| File                      | Description                                     |
|---------------------------|-------------------------------------------------|
| `01_maze_nightmare.txt`   | Complex maze with many dead ends                |
| `02_capacity_hell.txt`    | Highly restricted capacity on every link        |
| `03_ultimate_challenge.txt` | Large map combining all constraint types     |

### 💀 Challenger

| File                         | Description                                   |
|------------------------------|-----------------------------------------------|
| `01_the_impossible_dream.txt`| Extreme map pushing the solver to its limits  |

---

## 📚 Resources

### Technical References
- [pygame - youtube](https://www.youtube.com/watch?v=8J8wWxbAdFg&list=PLMS9Cy4Enq5KsM7GJ4LHnlBQKTQBV8kaR)
- [Pygame Documentation](https://www.pygame.org/docs/)
- [Recherche A-Star — youtube](https://www.youtube.com/watch?v=lSzElQ2Belk)
- [Comprendre A* — youtube](https://www.youtube.com/watch?v=i0x5fj4PqP4)
- [A* Search Algorithm — Wikipedia](https://en.wikipedia.org/wiki/A*_search_algorithm)

- [uv — youtube](https://www.youtube.com/watch?v=3WJ40TYi83c)

### AI Usage


| Task                        | Details                                                                 |
|-----------------------------|-------------------------------------------------------------------------|
| **Algorithm debugging**     | Identifying edge cases in the A* time-expanded state space              |
| **Bug fixes**               | various bug fixes |
| **Code quality**            | Resolving `mypy --strict` and `flake8` errors across all source files   |
| **Map design**              | Generating complex test maps (extreme maze, hardcore maze)               |
| **README**                  | Drafting this document                                                  |

> AI was used as a pair-programming assistant. All generated code was reviewed, understood, and adapted by the project author.
