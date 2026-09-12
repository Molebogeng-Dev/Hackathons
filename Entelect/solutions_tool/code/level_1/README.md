# Level 1 Solution - Photospheria Ecological Optimization

This package contains the Level 1 simulation engine, strategy planner, and submission files.

## Files
- `solution.json`: The generated submission file (802,101,053 points, 100% coverage, H = 0.999487).
- `1.json`: Level 1 map specification.
- `run.py`: Entrypoint to simulate, validate, and regenerate `solution.json`.
- `src/`: General-purpose modular simulation engine and planner.
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

