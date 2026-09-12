from __future__ import annotations
import math
from typing import Dict, List, Set, Tuple, Optional, Any
from .models import LevelConfig, CellState, PlantSpec, Submission, TickEntry, PlantAction, ScoreResult
from .geometry import get_spread_offsets, get_shade_offsets
from .loader import ResourceLoader
from .unlock_tree import UnlockTreeEvaluator, AnimalEvaluator

class SimulationEngine:
    def __init__(self, config: LevelConfig, loader: ResourceLoader):
        self.config = config
        self.loader = loader
        self.rows = config.rows
        self.cols = config.cols
        self.total_ticks = config.ticks
        self.animals_enabled = config.animals_enabled
        self.animal_evaluator = AnimalEvaluator(self.loader.animals, self.loader.classifications)

        # Deep copy initial grid state
        self.grid: Dict[Tuple[int, int], CellState] = {
            coord: cell.copy() for coord, cell in config.cells.items()
        }

        # Simulation tracking
        self.current_tick = 0
        self.current_season = "Spring"
        self.active_events: Set[str] = set()
        self.unlocked_species: Set[str] = {
            "Grass", "Rose Bush", "Lavender", "Dwarf Sunflower", "Oak Tree"
        }
        self.active_animals: Set[str] = set()

        # Build schedule command map: tick -> list of commands
        self.commands_by_tick: Dict[int, List[Dict[str, Any]]] = {}
        for cmd in config.commands:
            t = cmd.get("tick", 0)
            self.commands_by_tick.setdefault(t, []).append(cmd)

        # Precalculate habitable cells for starter plants (soil 0 or 1)
        self.habitable_coords = {
            coord for coord, cell in self.grid.items() if cell.soil in (0, 1)
        }

    def reset(self):
        self.grid = {
            coord: cell.copy() for coord, cell in self.config.cells.items()
        }
        self.current_tick = 0
        self.current_season = "Spring"
        self.active_events.clear()
        self.unlocked_species = {
            "Grass", "Rose Bush", "Lavender", "Dwarf Sunflower", "Oak Tree"
        }
        self.active_animals.clear()

    def run(self, submission: Submission) -> ScoreResult:
        self.reset()
        actions_by_tick: Dict[int, List[PlantAction]] = {
            entry.tick: entry.plants for entry in submission.actions
        }

        for tick in range(self.total_ticks):
            self.current_tick = tick
            player_actions = actions_by_tick.get(tick, [])
            self.step(player_actions)

        return self.calculate_score()

    def step(self, player_actions: List[PlantAction]):
        tick = self.current_tick

        # --- Phase 1: Environment / Season / Events ---
        if tick in self.commands_by_tick:
            for cmd in self.commands_by_tick[tick]:
                cmd_type = cmd.get("type", "")
                if cmd_type == "season":
                    self.current_season = cmd.get("season", self.current_season)
                elif cmd_type == "event":
                    self.active_events.add(cmd.get("event", ""))

        # Check unlocks
        self._update_unlocks()

        # --- Phase 2: Player Actions (Max 20) ---
        applied_actions = player_actions[:20]
        for act in applied_actions:
            coord = (act.row, act.col)
            if coord not in self.grid:
                continue  # Confirmed rule: silently drop invalid/unlisted coordinates

            spec = self.loader.plants.get(act.plant_index)
            if not spec:
                continue

            # Must be unlocked
            if spec.plant not in self.unlocked_species:
                continue

            # Soil match check (confirmed rule: placement legality is soil match)
            cell = self.grid[coord]
            if cell.soil not in spec.preferred_soil:
                continue

            # Overwrite incumbent plant
            cell.plant_index = act.plant_index
            cell.plant_age = 0
            cell.last_spread_tick = tick

        # --- Phase 3: Recalculate Shade ---
        self._recalculate_shade()

        # --- Phase 4: Autonomous Spread ---
        self._resolve_spreading(tick)

        # --- Phase 5: Immediate Shade Weakness Check ---
        for cell in self.grid.values():
            if cell.plant_index is not None and cell.is_shaded:
                spec = self.loader.plants.get(cell.plant_index)
                if spec:
                    for w in spec.weaknesses:
                        if w.get("type") == "no_shade_survival":
                            # Grass dies in shade
                            cell.plant_index = None
                            cell.plant_age = 0
                            cell.dead_matter = True
                            break

        # --- Phase 6: Nutrient Consumption & Regeneration ---
        for cell in self.grid.values():
            if cell.plant_index is not None:
                # Cell is occupied
                drain = 0.5 if cell.dead_matter else 1.0
                cell.nutrients -= drain
                if cell.nutrients <= 0.0:
                    # Plant dies of starvation
                    cell.nutrients = 0.0
                    cell.plant_index = None
                    cell.plant_age = 0
                    cell.dead_matter = True
            elif cell.dead_matter:
                # Cell is empty with dead matter: regenerate
                cell.nutrients = min(100.0, cell.nutrients + 1.0)

        # --- Phase 7: Plant Maturation & Lifespan Aging ---
        for cell in self.grid.values():
            if cell.plant_index is not None:
                cell.plant_age += 1

    def _recalculate_shade(self):
        # Reset shade
        for cell in self.grid.values():
            cell.is_shaded = False

        # Mature Oak Trees cast shade
        for (r, c), cell in self.grid.items():
            if cell.plant_index == 12:  # Oak Tree
                spec = self.loader.plants.get(12)
                if spec and cell.plant_age >= spec.growth.time_to_maturity:
                    # Cast shade radius 4
                    for dr, dc in get_shade_offsets(4):
                        target = (r + dr, c + dc)
                        if target in self.grid:
                            self.grid[target].is_shaded = True

    def _resolve_spreading(self, tick: int):
        # Determine which plants want to spread this tick
        spread_events: List[Tuple[Tuple[int, int], int]] = []  # (target_coord, plant_index)

        for (r, c), cell in self.grid.items():
            if cell.plant_index is None:
                continue

            spec = self.loader.plants.get(cell.plant_index)
            if not spec:
                continue

            growth = spec.growth
            # Check maturity
            if cell.plant_age < growth.time_to_maturity:
                continue

            # Check spread rate interval
            effective_spread_rate = growth.spread_rate
            # Check conditional modifiers (e.g. Orange Blossom in summer)
            for mod in growth.conditional_modifiers:
                if mod.get("condition") == f"season_{self.current_season.lower()}":
                    effective_spread_rate = mod.get("spread_rate", effective_spread_rate)

            # Check winter spread weakness
            if self.current_season == "Winter":
                has_winter_weakness = any(w.get("type") == "no_winter_spread" for w in spec.weaknesses)
                if has_winter_weakness:
                    continue

            # Check shade spread weakness
            if cell.is_shaded:
                has_shade_spread_weakness = any(w.get("type") == "no_shade_spread" for w in spec.weaknesses)
                if has_shade_spread_weakness:
                    continue

            # Check if this tick is a spread tick
            ticks_since_spread = tick - cell.last_spread_tick
            if ticks_since_spread >= effective_spread_rate:
                cell.last_spread_tick = tick
                offsets = get_spread_offsets(growth.spread_type, growth.spread_range)
                for dr, dc in offsets:
                    target_coord = (r + dr, c + dc)
                    if target_coord in self.grid:
                        target_cell = self.grid[target_coord]
                        # Target soil must match preferred soil
                        if target_cell.soil in spec.preferred_soil:
                            # Target must not be shaded if newcomer has shade weaknesses
                            if target_cell.is_shaded and any(
                                w.get("type") in ("no_shade_survival", "no_shade_spread") for w in spec.weaknesses
                            ):
                                continue
                            spread_events.append((target_coord, spec.index))

        # Apply spread: confirmed rule: newcomer overwrites incumbent plant
        for target_coord, p_idx in spread_events:
            target_cell = self.grid[target_coord]
            target_cell.plant_index = p_idx
            target_cell.plant_age = 0
            target_cell.last_spread_tick = tick

    def _update_unlocks(self):
        # Evaluates animals and unlock trees
        counts: Dict[str, int] = {}
        coverages: Dict[str, float] = {}
        alive_total = 0

        for cell in self.grid.values():
            if cell.plant_index is not None:
                spec = self.loader.plants.get(cell.plant_index)
                if spec:
                    counts[spec.plant] = counts.get(spec.plant, 0) + 1
                    alive_total += 1

        total_cells = self.rows * self.cols
        for plant_name, cnt in counts.items():
            coverages[plant_name] = cnt / total_cells if total_cells > 0 else 0.0

        dead_matter_count = sum(1 for c in self.grid.values() if c.dead_matter)
        burnt_soil_count = sum(1 for c in self.grid.values() if c.soil == 3)
        context = {
            "plant_counts": counts,
            "plant_coverages": coverages,
            "total_cells": total_cells,
            "total_alive": alive_total,
            "feature_counts": {
                "dead_matter": dead_matter_count,
                "burnt_soil": burnt_soil_count
            }
        }

        # Update animals if enabled
        if self.animals_enabled:
            self.active_animals = self.animal_evaluator.evaluate_all(context)

        evaluator = UnlockTreeEvaluator(
            unlocked_species=self.unlocked_species,
            active_animals=self.active_animals,
            active_events=self.active_events
        )

        # Multi-pass cascade
        changed = True
        while changed:
            changed = False
            for item in self.loader.unlock_conditions:
                p_name = item.get("plant", "")
                if p_name not in self.unlocked_species:
                    if evaluator.evaluate(item.get("unlock", {}), context):
                        self.unlocked_species.add(p_name)
                        evaluator.unlocked_species.add(p_name)
                        changed = True

    def calculate_score(self) -> ScoreResult:
        # Tally final state at tick T
        species_counts: Dict[int, int] = {}
        total_alive = 0
        longevity_sum = 0.0

        T = self.total_ticks
        c_max = self.rows * self.cols

        for cell in self.grid.values():
            if cell.plant_index is not None:
                idx = cell.plant_index
                species_counts[idx] = species_counts.get(idx, 0) + 1
                total_alive += 1
                longevity_sum += cell.plant_age

        if total_alive == 0:
            return ScoreResult(
                alive_count=0,
                max_cells=c_max,
                entropy=0.0,
                main_score=0.0,
                longevity_score=0.0,
                final_score=0.0,
                leaderboard_score=0,
                species_distribution={}
            )

        # Shannon Entropy with base N = 31 (exact server formula)
        N = 31
        entropy = 0.0
        for idx, count in species_counts.items():
            p_i = count / total_alive
            if p_i > 0:
                entropy -= p_i * (math.log(p_i) / math.log(N))

        # Sample size factor (density_factor): C / C_max
        density_factor = total_alive / c_max
        main_score = entropy * density_factor

        # Longevity score: sum(age) / (C_max * T)
        longevity_score = longevity_sum / (c_max * T)

        # Final weighted score
        final_score = 0.8 * main_score + 0.2 * longevity_score
        leaderboard_score = int(round(final_score * 1_000_000_000))

        return ScoreResult(
            alive_count=total_alive,
            max_cells=c_max,
            entropy=entropy,
            main_score=main_score,
            longevity_score=longevity_score,
            final_score=final_score,
            leaderboard_score=leaderboard_score,
            species_distribution=species_counts
        )

