#!/usr/bin/env python3
"""
Photospheria Level 4: Forest Ecosystem Solver & Evaluator
"""
import argparse
import json
import os
import sys

# Ensure src/ is on Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from core.loader import ResourceLoader
from core.engine import SimulationEngine
from strategies.level4_expert import Level4ExpertStrategy


def main():
    parser = argparse.ArgumentParser(description="Photospheria Level 4 Solver & Evaluator")
    parser.add_argument("--level", default="4.json", help="Path to level map JSON (default: 4.json)")
    parser.add_argument("--output", default="solution.json", help="Output solution path (default: solution.json)")
    parser.add_argument("--key-mode", default="DUAL", choices=["DUAL", "PLANT_INDEX", "INDEX"],
                        help="Key naming mode (default: DUAL for maximum compatibility)")
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    level_path = os.path.join(base_dir, args.level) if not os.path.isabs(args.level) else args.level
    out_path = os.path.join(base_dir, args.output) if not os.path.isabs(args.output) else args.output

    loader = ResourceLoader(base_dir)
    config = loader.load_level(level_path)

    strategy = Level4ExpertStrategy(config, loader)
    submission = strategy.solve()

    engine = SimulationEngine(config, loader)
    result = engine.run(submission)

    habitable_count = len([c for c in config.cells.values() if c.soil in (0, 1)])
    coverage_pct = (result.alive_count / habitable_count * 100) if habitable_count > 0 else 0

    print("=" * 60)
    print("       LEVEL 4: FOREST ECOSYSTEM SCORE REPORT        ")
    print("=" * 60)
    print(f"Habitable Cells Covered: {result.alive_count} / {habitable_count} ({coverage_pct:.2f}%)")
    print(f"Shannon Diversity (H):   {result.entropy:.6f} / 1.000000")
    print(f"Main Diversity Score:    {result.main_score:.6f}")
    print(f"Longevity Score:         {result.longevity_score:.6f}")
    print(f"Final Score:             {result.final_score:.6f}")
    print(f"★ LEADERBOARD SCORE:     {result.leaderboard_score:,} pts")
    print(f"Species Distribution:    {result.species_distribution}")
    print("=" * 60)

    # Save solution
    with open(out_path, "w") as f:
        json.dump(submission.to_dict(mode=args.key_mode), f, indent=2)
    print(f"\n[Saved Level 4 solution to {out_path} (mode: {args.key_mode})]")

    score_path = os.path.join(base_dir, "score.json")
    with open(score_path, "w") as f:
        json.dump({
            "level": 4,
            "alive_count": result.alive_count,
            "habitable_count": habitable_count,
            "coverage_pct": coverage_pct,
            "entropy": result.entropy,
            "main_score": result.main_score,
            "longevity_score": result.longevity_score,
            "final_score": result.final_score,
            "leaderboard_score": result.leaderboard_score,
            "species_distribution": {str(k): v for k, v in result.species_distribution.items()}
        }, f, indent=2)


if __name__ == "__main__":
    main()
