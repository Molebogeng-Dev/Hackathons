# Photospheria Level 3: Park Potential — Multi-Level Solution

## Overview
This package contains the high-performance ecological simulation and optimization system for **Level 3 ("Park Potential")** of the Entelect Photospheria hackathon challenge, along with the unified multi-level scoring dashboard covering Levels 1, 2, and 3.

---

## Performance & Leaderboard Summary

| Level | Environment | Grid Size | Ticks | Habitable Coverage | Shannon Entropy (H) | Standalone Score |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Level 1** | Greenhouse Study | $50 \times 50$ | 500 | 700 / 700 (100.0%) | 0.998894 | **801,631,386 pts** |
| **Level 2** | Garden Growth Study | $70 \times 100$ | 500 | 926 / 926 (100.0%) | 0.999781 | **802,133,259 pts** |
| **Level 3** | Park Potential | $150 \times 150$ | 800 | 4,080 / 4,280 (95.33%) | 0.997284 | **765,342,469 pts** |
| **TOTAL** | **Combined Leaderboard Score** | — | — | — | — | **★ 2,369,107,114 pts** |

**Progress to 4 Billion Target**: **59.23% achieved** across the first 3 levels (averaging ~790M pts/level).

---

## Key Algorithmic Innovations for Level 3

### 1. Spatial Zoning Architecture
In Level 3, the grid scales to $150 \times 150$ with 4,921 cells. Naive planting causes:
- Oak Trees to cast shade across the board, killing Grass (`no_shade_survival`) and halting Dwarf Sunflower spreading (`no_shade_spread`).
- Grass to spread uncontrollably every 2 ticks, overwriting slower species into monoculture.

To solve this, our **Spatial Zoning Strategy** partitions the habitable cells into 5 non-overlapping spatial bands:
- **Zone 0 (Rows 0–29)**: Oak Tree (designated canopy sector).
- **Zone 1 (Rows 6–59)**: Dwarf Sunflower.
- **Zone 2 (Rows 30–89)**: Rose Bush.
- **Zone 3 (Rows 63–140)**: Lavender.
- **Zone 4 (Rows 120–149)**: Grass.

This guarantees:
- **Zero Shade Mortality**: Grass and Sunflowers are completely separated from Oak Trees.
- **Zero Inter-Species Overwrites**: Species expand into their own sectors without destroying neighbors.

### 2. Winter Propagation & Controlled Spreading
At tick 700, the season transitions to **Winter**:
- Rose Bush and Lavender have `no_winter_spread`, so their counts remain strictly stable where planted.
- Oak Tree (spread rate 7) and Dwarf Sunflower (spread rate 4) expand steadily to tile the remaining unplanted cells.
- Grass (spread rate 2) is seeded with controlled timing so it covers its zone without runaway expansion.

### 3. Starvation Elimination via Late-Placement Window
- Plants starve and die after 100 consecutive ticks without soil replenishment.
- By placing all actions in the final 99 ticks ($t = 701 \dots 799$), **zero plants starve to death**, and all active plants survive to the final evaluation tick ($T = 800$).

---

## Directory Structure
```
level_3/
├── 1.json                     # Level 1 map data
├── 2.json                     # Level 2 map data
├── 3.json                     # Level 3 map data
├── additional-resources/      # Plant encyclopedia, animals, classifications, unlocks
├── run.py                     # Unified multi-level simulation & scoring dashboard
├── solution.json              # Level 3 submission file (dual-key format)
├── README.md                  # Documentation & verification report
└── src/
    ├── core/
    │   ├── engine.py          # High-performance simulation engine with fast-path & animals
    │   ├── geometry.py        # Neighborhood offsets & shade radius geometry
    │   ├── loader.py          # Universal resource & map loader
    │   ├── models.py          # Data models with dual-key serialization
    │   └── unlock_tree.py     # Recursive unlock condition evaluator
    ├── strategies/
    │   ├── base.py            # Abstract strategy interface
    │   ├── level1_expert.py   # Level 1 strategy
    │   ├── level2_expert.py   # Level 2 strategy
    │   └── level3_expert.py   # Level 3 spatial zoning strategy
    └── tests/
        └── test_engine.py     # Automated validation & scoring unit tests
```

---

## Quickstart & Verification

### Run Multi-Level Dashboard
```bash
python3 run.py
```
Outputs standalone scores for Level 1, Level 2, and Level 3, along with the combined cumulative leaderboard score.

### Generate Level 3 Solution Only
```bash
python3 run.py --level 3 --output solution.json
```

### Run Unit Tests
```bash
python3 -m unittest discover -s src/tests
```

---

## Submission Format
The generated `solution.json` contains dual-key actions (`"plant_index"` and `"index"`) ensuring full compatibility with portal schema validators:
```json
{
  "actions": [
    {
      "tick": 701,
      "plants": [
        {
          "plant_index": 12,
          "index": 12,
          "row": 18,
          "col": 4
        }
      ]
    }
  ]
}
```
All constraints are strictly satisfied:
- $\le 20$ plants per tick.
- Valid coordinates within `3.json`.
- Soil types match species preferred soil.
- Ticks $701 \dots 799$ within $[0, T-1]$.

