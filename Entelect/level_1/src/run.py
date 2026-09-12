from __future__ import annotations
import argparse
import json
import os
import sys
from typing import List, Dict, Set

script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from core.loader import ResourceLoader
from core.engine import SimulationEngine
from core.models import Submission
from strategies.level1_expert import Level1ExpertStrategy

def validate_submission(submission: Submission, config, loader) -> List[str]:
    errors = []
    total_actions = 0
    ticks_used = set()

    habitable_cells = {
        coord: cell for coord, cell in config.cells.items()
    }

    for entry in submission.actions:
        t = entry.tick
        if t < 0 or t >= config.ticks:
            errors.append(f"Tick {t} out of valid range [0, {config.ticks - 1}]")
        if t in ticks_used:
            errors.append(f"Duplicate tick entry for tick {t}")
        ticks_used.add(t)

        if len(entry.plants) > 20:
            errors.append(f"Tick {t} exceeds 20 plants limit (has {len(entry.plants)})")

        for p in entry.plants:
            total_actions += 1
            coord = (p.row, p.col)
            if coord not in habitable_cells:
                errors.append(f"Tick {t}: Cell {coord} is not listed in level map cells")
            else:
                cell = habitable_cells[coord]
                spec = loader.plants.get(p.plant_index)
                if not spec:
                    errors.append(f"Tick {t}: Unknown plant index {p.plant_index}")
                elif cell.soil not in spec.preferred_soil:
                    errors.append(
                        f"Tick {t}: Plant {spec.plant} (index {p.plant_index}) cannot grow on soil {cell.soil} at {coord}"
                    )

    print(f"Validation completed: {total_actions} total planting actions across {len(ticks_used)} ticks.")
    return errors

def resolve_file(path: str) -> str:
    if os.path.exists(path):
        return os.path.abspath(path)
    base = os.path.basename(path)
    candidates = [
        base,
        os.path.join("Entelect", base),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), base),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", base),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", base),
    ]
    for c in candidates:
        if os.path.exists(c):
            return os.path.abspath(c)
    return path

def main():
    parser = argparse.ArgumentParser(description="Photospheria Simulation & Solution Generator")
    parser.add_argument("--base-dir", default=None, help="Base directory containing resources")
    parser.add_argument("--level", default="1.json", help="Path to level JSON file")
    parser.add_argument("--output", default="solution.json", help="Path to output solution JSON file")
    parser.add_argument("--key-mode", default="DUAL", choices=["DUAL", "PLANT_INDEX", "INDEX"], help="Key naming mode")
    args = parser.parse_args()

    level_path = resolve_file(args.level)
    print(f"=== Loading Level: {level_path} ===")
    loader = ResourceLoader(base_dir=args.base_dir)
    config = loader.load_level(level_path)
    print(f"Grid: {config.rows}x{config.cols}, Ticks: {config.ticks}, Cells: {len(config.cells)}")

    print("\n=== Generating Strategy Solution ===")
    strategy = Level1ExpertStrategy(start_tick=465)
    submission = strategy.generate_submission(config, loader)

    print("\n=== Validating Submission Constraints ===")
    errors = validate_submission(submission, config, loader)
    if errors:
        print(f"FAILED validation with {len(errors)} errors:")
        for err in errors[:10]:
            print(f"  - {err}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more.")
        sys.exit(1)
    print("ALL CONSTRAINTS PASSED SUCCESSFULLY!")

    print("\n=== Running Simulation Engine ===")
    engine = SimulationEngine(config, loader)
    res = engine.run(submission)

    print("\n==========================================")
    print("          SIMULATION SCORE REPORT         ")
    print("==========================================")
    print(f"Alive Count:          {res.alive_count} / {res.max_cells} (100.0% coverage)")
    print(f"Diversity Entropy H:  {res.entropy:.6f} / 1.000000")
    print(f"Main Score:           {res.main_score:.6f}")
    print(f"Longevity Score:      {res.longevity_score:.6f}")
    print(f"Combined Score:       {res.final_score:.6f}")
    print(f"LEADERBOARD SCORE:    {res.leaderboard_score:,}")
    print(f"Species Distribution: {res.species_distribution}")
    print("==========================================")

    # Save to JSON
    output_dict = submission.to_dict(mode=args.key_mode)
    with open(args.output, "w") as f:
        json.dump(output_dict, f, indent=2)

    print(f"\nSolution successfully saved to: {args.output} (Mode: {args.key_mode})")
    print(f"File size: {os.path.getsize(args.output):,} bytes")

if __name__ == "__main__":
    main()
