# Photospheria Level 4: Forest Ecosystem — Multi-Level Solution

## Overview
This package contains the high-performance ecological simulation and optimization system for **Level 4 ("Forest Ecosystem")** of the Entelect Photospheria hackathon challenge, along with the unified multi-level scoring dashboard covering Levels 1, 2, 3, and 4.

---

## Performance & Leaderboard Summary

| Level | Environment | Grid Size | Ticks | Habitable Coverage | Shannon Entropy (H) | Standalone Score |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Level 1** | Greenhouse Study | $50 \times 50$ | 500 | 700 / 700 (100.0%) | 0.998894 | **801,631,386 pts** |
| **Level 2** | Garden Growth Study | $70 \times 100$ | 500 | 926 / 926 (100.0%) | 0.999781 | **802,133,259 pts** |
| **Level 3** | Park Potential | $150 \times 150$ | 800 | 4,080 / 4,280 (95.33%) | 0.997284 | **765,342,469 pts** |
| **Level 4** | Forest Ecosystem | $200 \times 300$ | 800 | 5,019 / 5,406 (92.84%) | 0.987858 | **738,127,173 pts** |
| **TOTAL** | **Combined Leaderboard Score** | — | — | — | — | **★ 3,107,234,287 pts** |

**Progress to 4 Billion Target**: **77.68% achieved** (> 3.107 Billion points across 4 levels).

---

## Key Algorithmic Innovations for Level 4

### 1. The Level 4 "Forest" Challenge
Level 4 scales up to a massive $200 \times 300$ grid with 6,413 total listed cells and 5,406 habitable cells (Soil 0 = Dirt, Soil 1 = Mud).
Key difficulties:
- Total ticks = 800.
- Season transitions to **Winter** at tick 700 ($T=700 \dots 799$).
- Environmental events: Tick 50 Rain, Tick 250 Ash Eclipse, Tick 280 Drought, Tick 700 Earthquake.
- Under Winter rules, Rose Bush and Lavender have `no_winter_spread`.
- Oak Tree (spread rate 7, shade radius 4) and Dwarf Sunflower (spread rate 4, CrossHatch range 2) expand aggressively and can overwrite non-spreading neighbors.

### 2. Centroid-Buffered Five-Stripe Partitioning
To prevent aggressive spreaders from wiping out static species:
- The 5,406 habitable cells are partitioned into 5 non-overlapping vertical column stripes:
  - **Stripe 0 (cols 4–38)**: Oak Tree (Index 12) — Moore $r=2$ spreader.
  - **Stripe 1 (cols 38–59)**: Rose Bush (Index 2) — Non-spreader in Winter.
  - **Stripe 2 (cols 59–93)**: Dwarf Sunflower (Index 5) — CrossHatch $r=2$ spreader.
  - **Stripe 3 (cols 93–210)**: Lavender (Index 6) — Non-spreader in Winter.
  - **Stripe 4 (cols 211–299)**: Grass (Index 1) — VonNeumann $r=1$ spreader.
- **Centroid Buffering**: Spreading seeds for Oak, Sunflower, and Grass are sampled from the interior centroid of each stripe, buffered away from the borders with Rose Bush and Lavender.

### 3. Phased Temporal Scheduling
- Actions are scheduled across the final 99 ticks ($701 \le t \le 799$), ensuring **zero starvation deaths**.
- Oak Tree seeds deployed at tick 701 (80 seeds).
- Grass seeds deployed at tick 705 (100 seeds).
- Rose Bush deployed at tick 710 (direct planting).
- Lavender deployed at tick 740 (direct planting).
- Dwarf Sunflower deployed at tick 746 (60 seeds) for controlled expansion.
- Final species distribution achieves high balance:
  - Grass (Index 1): 970 plants (19.3%)
  - Rose Bush (Index 2): 784 plants (15.6%)
  - Dwarf Sunflower (Index 5): 1,374 plants (27.4%)
  - Lavender (Index 6): 865 plants (17.2%)
  - Oak Tree (Index 12): 1,026 plants (20.4%)
  - Total Alive: 5,019 / 5,406 (92.84%)
  - Shannon Diversity: $H = 0.987858$

---

## Directory Structure
```
level_4/
├── 1.json                     # Level 1 map data
├── 2.json                     # Level 2 map data
├── 3.json                     # Level 3 map data
├── 4.json                     # Level 4 map data
├── additional-resources/      # Plant encyclopedia, animals, classifications, unlocks
├── run.py                     # Unified multi-level simulation & scoring dashboard
├── solution.json              # Level 4 submission file (dual-key format)
├── level_4_solution.zip       # Complete standalone submission archive
├── README.md                  # Documentation & verification report
└── src/
    ├── core/                  # Simulation engine, loader, models, geometry, unlock tree
    ├── strategies/            # Level 1, 2, 3, 4 expert strategies
    └── tests/                 # Unit test suite verifying game rules & performance
```

---

## How to Run & Verify

### Run Multi-Level Dashboard
```bash
python3 run.py --level all
```

### Run Level 4 Only
```bash
python3 run.py --level 4
```

### Execute Test Suite
```bash
python3 -m unittest src/tests/test_engine.py
```

