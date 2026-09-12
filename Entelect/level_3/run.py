#!/usr/bin/env python3
import argparse
import json
import os
import sys

# Ensure src/ is on Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from core.loader import ResourceLoader
from core.engine import SimulationEngine
from strategies.level1_expert import Level1ExpertStrategy
from strategies.level2_expert import Level2ExpertStrategy
from strategies.level3_expert import Level3ExpertStrategy

def evaluate_level(level_num: int, level_file: str, strategy, loader: ResourceLoader):
    config = loader.load_level(level_file)
    engine = SimulationEngine(config, loader)
    submission = strategy.generate_submission(config, loader)
    score_result = engine.run(submission)
    return config, submission, score_result

def main():
    parser = argparse.ArgumentParser(description="Photospheria Multi-Level Solver & Evaluator")
    parser.add_argument("--level", choices=["1", "2", "3", "all"], default="all",
                        help="Level to simulate and score ('1', '2', '3', or 'all' for multi-level dashboard)")
    parser.add_argument("--output", type=str, default="solution.json",
                        help="Path to save the generated solution JSON (default: solution.json)")
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    loader = ResourceLoader(base_dir)

    print("=" * 66)
    print("           PHOTOSPHERIA MULTI-LEVEL SIMULATION DASHBOARD          ")
    print("=" * 66)

    scores = {}

    # --- Level 1 ---
    if args.level in ("1", "all"):
        lvl1_file = os.path.join(base_dir, "1.json")
        config1, sub1, res1 = evaluate_level(1, lvl1_file, Level1ExpertStrategy(), loader)
        scores[1] = res1.leaderboard_score
        c_max1 = len([c for c in config1.cells.values() if c.soil in (0, 1)])
        cov1 = (res1.alive_count / c_max1 * 100) if c_max1 > 0 else 0
        print(f"\n>>> Level 1: Greenhouse Study (50x50, T=500)")
        print(f"     Habitable Cells Covered: {res1.alive_count} / {c_max1} ({cov1:.2f}%)")
        print(f"     Shannon Diversity (H):   {res1.entropy:.6f}")
        print(f"     Main Diversity Score:    {res1.main_score:.6f}")
        print(f"     Longevity Score:         {res1.longevity_score:.6f}")
        print(f"     ★ Level 1 Standalone:    {res1.leaderboard_score:,} pts")
        if args.level == "1":
            with open(args.output, "w") as f:
                json.dump(sub1.to_dict(), f, indent=2)
            print(f"\n[Saved Level 1 solution to {args.output}]")

    # --- Level 2 ---
    if args.level in ("2", "all"):
        lvl2_file = os.path.join(base_dir, "2.json")
        config2, sub2, res2 = evaluate_level(2, lvl2_file, Level2ExpertStrategy(), loader)
        scores[2] = res2.leaderboard_score
        c_max2 = len([c for c in config2.cells.values() if c.soil in (0, 1)])
        cov2 = (res2.alive_count / c_max2 * 100) if c_max2 > 0 else 0
        print(f"\n>>> Level 2: Garden Growth Study (70x100, T=500)")
        print(f"     Habitable Cells Covered: {res2.alive_count} / {c_max2} ({cov2:.2f}%)")
        print(f"     Shannon Diversity (H):   {res2.entropy:.6f}")
        print(f"     Main Diversity Score:    {res2.main_score:.6f}")
        print(f"     Longevity Score:         {res2.longevity_score:.6f}")
        print(f"     ★ Level 2 Standalone:    {res2.leaderboard_score:,} pts")
        if args.level == "2":
            with open(args.output, "w") as f:
                json.dump(sub2.to_dict(), f, indent=2)
            print(f"\n[Saved Level 2 solution to {args.output}]")

    # --- Level 3 ---
    if args.level in ("3", "all"):
        lvl3_file = os.path.join(base_dir, "3.json")
        config3, sub3, res3 = evaluate_level(3, lvl3_file, Level3ExpertStrategy(), loader)
        scores[3] = res3.leaderboard_score
        c_max3 = len([c for c in config3.cells.values() if c.soil in (0, 1)])
        cov3 = (res3.alive_count / c_max3 * 100) if c_max3 > 0 else 0
        print(f"\n>>> Level 3: Park Potential (150x150, T=800)")
        print(f"     Habitable Cells Covered: {res3.alive_count} / {c_max3} ({cov3:.2f}%)")
        print(f"     Shannon Diversity (H):   {res3.entropy:.6f}")
        print(f"     Main Diversity Score:    {res3.main_score:.6f}")
        print(f"     Longevity Score:         {res3.longevity_score:.6f}")
        print(f"     Species Distribution:    {res3.species_distribution}")
        print(f"     ★ Level 3 Standalone:    {res3.leaderboard_score:,} pts")

        # Save Level 3 solution
        out_path = args.output if args.level == "3" else os.path.join(base_dir, "solution.json")
        with open(out_path, "w") as f:
            json.dump(sub3.to_dict(), f, indent=2)
        print(f"\n[Saved Level 3 solution to {out_path}]")

    # --- Multi-Level Leaderboard Summary ---
    if args.level == "all":
        combined_total = sum(scores.values())
        target_4b = 4_000_000_000
        progress_pct = (combined_total / target_4b) * 100

        print("\n" + "=" * 66)
        print("                     LEADERBOARD SUMMARY                          ")
        print("=" * 66)
        print(f"  • Level 1 Standalone Score:       {scores.get(1, 0):>14,} pts")
        print(f"  • Level 2 Standalone Score:       {scores.get(2, 0):>14,} pts")
        print(f"  • Level 3 Standalone Score:       {scores.get(3, 0):>14,} pts")
        print("  " + "-" * 62)
        print(f"  ★ COMBINED TOTAL SCORE:          {combined_total:>14,} pts")
        print(f"  🎯 Target (4 Billion):           {target_4b:>14,} pts ({progress_pct:.2f}% achieved)")
        print("=" * 66)

if __name__ == "__main__":
    main()

