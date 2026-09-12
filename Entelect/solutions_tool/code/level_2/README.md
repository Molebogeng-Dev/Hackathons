# Level 2 Solution - Photospheria Garden Growth Study

This package contains the Level 2 simulation engine, strategy planner, and submission files.

## Leaderboard Scores
- **Level 2 Alone**: 802,248,798 points (100% habitable coverage, H = 0.999926)
- **Level 1 Alone**: 802,368,602 points
- **Combined Cumulative Score**: **1,604,617,400 points** (> 1.6 Billion points!)

## Files
- `solution.json`: The generated Level 2 submission JSON file.
- `2.json`: Level 2 map specification (70x100 grid).
- `1.json`: Level 1 map specification (used for combined score reporting).
- `run.py`: Entrypoint to simulate, validate, and regenerate `solution.json`.
- `src/`: Modular simulation engine, unlock tree evaluator, and level strategies.
- `additional-resources/`: Plant encyclopedia, animal interactions, and unlock conditions.

## How to Run
Run directly from this directory:
```bash
python3 run.py
```

To switch key format if required by the submission portal:
```bash
# Dual keys (default):
python3 run.py --key-mode DUAL

# Plant index only:
python3 run.py --key-mode PLANT_INDEX

# Index only:
python3 run.py --key-mode INDEX
```

