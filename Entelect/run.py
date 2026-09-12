#!/usr/bin/env python3
"""
Photospheria Master Multi-Level Solver & Evaluator
Unified entry point to run, score, and package all levels (1, 2, 3, 4).
Dynamically calculates standalone scores, cumulative multi-level totals,
and automatically synchronizes solutions/ with updated JSON and ZIP archives.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import zipfile
from typing import Dict, Any, Optional

LEVELS = [1, 2, 3, 4]
LEVEL_NAMES = {
    1: "Greenhouse Study",
    2: "Garden Growth Study",
    3: "Park Potential",
    4: "Forest Ecosystem"
}

def zip_level(level_dir: str, zip_path: str):
    """Packages the level directory into a clean, standalone ZIP archive."""
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(level_dir):
            dirs[:] = [d for d in dirs if d != "__pycache__" and not d.endswith(".egg-info")]
            for f in files:
                if f.endswith(".pyc") or f.endswith(".DS_Store") or f == "score.json":
                    continue
                fp = os.path.join(root, f)
                rel_path = os.path.relpath(fp, level_dir)
                zf.write(fp, rel_path)

def run_level(level_num: int, base_dir: str) -> Optional[Dict[str, Any]]:
    """Runs a level's solver and evaluator, returns its score dictionary, and syncs solutions."""
    level_dir = os.path.join(base_dir, f"level_{level_num}")
    run_script = os.path.join(level_dir, "run.py")
    if not os.path.exists(run_script):
        print(f"Error: {run_script} not found.")
        return None

    print(f"\n{'='*68}")
    print(f"       RUNNING & EVALUATING LEVEL {level_num}: {LEVEL_NAMES.get(level_num, '').upper()}")
    print(f"{'='*68}")
    res = subprocess.run([sys.executable, run_script], cwd=level_dir)
    if res.returncode != 0:
        print(f"Error executing level {level_num} runner.")
        return None

    # Load score metrics
    score_file = os.path.join(level_dir, "score.json")
    score_data = None
    if os.path.exists(score_file):
        with open(score_file, "r") as f:
            score_data = json.load(f)

    # Synchronize solutions directory and solutions_tool directory
    for s_dir_name in ["solutions", "solutions_tool"]:
        s_dir = os.path.join(base_dir, s_dir_name)
        os.makedirs(s_dir, exist_ok=True)

        # 1. Copy solution.json -> level_{X}_solution.json
        sol_src = os.path.join(level_dir, "solution.json")
        sol_dst = os.path.join(s_dir, f"level_{level_num}_solution.json")
        if os.path.exists(sol_src):
            shutil.copyfile(sol_src, sol_dst)

        # 2. Package level_{X} -> level_{X}_solution.zip
        zip_dst = os.path.join(s_dir, f"level_{level_num}_solution.zip")
        zip_level(level_dir, zip_dst)

    # Sync code tree in solutions_tool/code
    code_dst = os.path.join(base_dir, "solutions_tool", "code", f"level_{level_num}")
    if os.path.exists(code_dst):
        shutil.rmtree(code_dst)
    shutil.copytree(
        level_dir,
        code_dst,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "score.json", ".pytest_cache")
    )
    shutil.copyfile(
        os.path.join(base_dir, "run.py"),
        os.path.join(base_dir, "solutions_tool", "code", "run.py")
    )

    print(f"[Sync] Updated solutions/ & solutions_tool/ for Level {level_num} (JSON, ZIP, and code)")
    return score_data

def main():
    parser = argparse.ArgumentParser(description="Photospheria Master Multi-Level Dashboard")
    parser.add_argument("--level", choices=["1", "2", "3", "4", "all"], default="all",
                        help="Level to evaluate ('1', '2', '3', '4', or 'all' for complete multi-level dashboard)")
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.abspath(__file__))

    print("=" * 72)
    print("           PHOTOSPHERIA MULTI-LEVEL SIMULATION DASHBOARD          ")
    print("=" * 72)

    levels_to_run = LEVELS if args.level == "all" else [int(args.level)]
    scores = {}

    for lvl in levels_to_run:
        score = run_level(lvl, base_dir)
        if score:
            scores[lvl] = score

    # Also read existing score.json for levels not run if single level selected
    for lvl in LEVELS:
        if lvl not in scores:
            score_file = os.path.join(base_dir, f"level_{lvl}", "score.json")
            if os.path.exists(score_file):
                with open(score_file, "r") as f:
                    scores[lvl] = json.load(f)

    # Print Leaderboard Summary
    print("\n" + "=" * 76)
    print("                     LEADERBOARD SCOREBOARD SUMMARY                       ")
    print("=" * 76)
    print(f"{'Level':<10} {'Habitable Covered':<20} {'Entropy (H)':<14} {'Standalone Score':<18} {'Cumulative Total'}")
    print("-" * 76)

    cumulative = 0
    for lvl in LEVELS:
        if lvl in scores:
            sc = scores[lvl]
            standalone = sc.get("leaderboard_score", 0)
            cumulative += standalone
            hab = f"{sc.get('alive_count', 0)} / {sc.get('habitable_count', 0)}"
            h = f"{sc.get('entropy', 0):.6f}"
            print(f"Level {lvl:<4} {hab:<20} {h:<14} {standalone:>14,} pts   {cumulative:>14,} pts")
        else:
            print(f"Level {lvl:<4} {'N/A':<20} {'N/A':<14} {'N/A':>14}       {'N/A':>14}")

    print("-" * 76)
    print(f"★ GRAND COMBINED TOTAL SCORE:                       {cumulative:>14,} pts")
    print("=" * 76)
    print("\nAll synchronized submissions ready in Entelect/solutions/:")
    for lvl in LEVELS:
        print(f"  • Level {lvl}: solutions/level_{lvl}_solution.zip & solutions/level_{lvl}_solution.json")


if __name__ == "__main__":
    main()

