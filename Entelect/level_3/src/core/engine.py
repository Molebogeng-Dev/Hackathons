from __future__ import annotations
import math
import operator
from typing import Dict, List, Set, Tuple, Optional, Any
from .models import LevelConfig, CellState, PlantSpec, Submission, TickEntry, PlantAction, ScoreResult
from .geometry import get_spread_offsets, get_shade_offsets
from .loader import ResourceLoader
from .unlock_tree import UnlockTreeEvaluator

OPS = {
    ">=": operator.ge,
    ">": operator.gt,
    "<=": operator.le,
    "<": operator.lt,
    "==": operator.eq,
    "=": operator.eq
}

def check_animal_condition(cond: Dict[str, Any], context: Dict[str, Any], classifications: Dict[str, List[str]]) -> bool:
    c_type = cond.get("type", "")
    op_func = OPS.get(cond.get("operator", ">="), operator.ge)
    threshold = cond.get("threshold", 0)
    
    if c_type == "coverage":
        species_list = cond.get("species", [])
        total_cov = sum(context["plant_coverages"].get(s, 0.0) for s in species_list)
        return op_func(total_cov, threshold)
        
    elif c_type == "count":
        if "species" in cond:
            species = cond["species"]
            cnt = context["plant_counts"].get(species, 0)
            return op_func(cnt, threshold)
        elif "species_group" in cond:
            groups = cond["species_group"]
            all_species = set()
            for g in groups:
                if g in classifications:
                    all_species.update(classifications[g])
                else:
                    all_species.add(g)
            cnt = sum(context["plant_counts"].get(s, 0) for s in all_species)
            return op_func(cnt, threshold)
            
    elif c_type == "group_coverage":
        groups = cond.get("species_group", [])
        all_species = set()
        for g in groups:
            if g in classifications:
                all_species.update(classifications[g])
            else:
                all_species.add(g)
        total_cov = sum(context["plant_coverages"].get(s, 0.0) for s in all_species)
        return op_func(total_cov, threshold)
        
    elif c_type == "dominance":
        total_alive = context.get("total_alive", 0)
        if total_alive == 0:
            return False
        max_species_cnt = max(context["plant_counts"].values()) if context["plant_counts"] else 0
        return (max_species_cnt / total_alive) >= threshold

    return False

def check_animal_requirements(req: Dict[str, Any], context: Dict[str, Any], classifications: Dict[str, List[str]]) -> bool:
    req_type = req.get("type", "AND").upper()
    conds = req.get("conditions", [])
    if req_type == "AND":
        return all(check_animal_condition(c, context, classifications) for c in conds)
    elif req_type == "OR":
        return any(check_animal_condition(c, context, classifications) for c in conds)
    return False


class SimulationEngine:
    def __init__(self, config: LevelConfig, loader: ResourceLoader):
        self.config = config
        self.loader = loader
        self.rows = config.rows
        self.cols = config.cols
        self.total_ticks = config.ticks
        self.animals_enabled = config.animals_enabled

        # Deep copy initial grid state
        self.grid: Dict[Tuple[int, int], CellState] = {
            coord: cell.copy() for coord, cell in config.cells.items()
        }

        # Fast tracking sets
        self.occupied_coords: Set[Tuple[int, int]] = set()
        self.tree_coords: Set[Tuple[int, int]] = set()
        self.dead_matter_coords: Set[Tuple[int, int]] = set()

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
        self.occupied_coords.clear()
        self.tree_coords.clear()
        self.dead_matter_coords.clear()
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

        # Check animal appearances & species unlocks
        self._update_animals_and_unlocks()

        # --- Phase 2: Player Actions (Max 20) ---
        applied_actions = player_actions[:20]
        for act in applied_actions:
            coord = (act.row, act.col)
            if coord not in self.grid:
                continue

            spec = self.loader.plants.get(act.plant_index)
            if not spec:
                continue

            if spec.plant not in self.unlocked_species:
                continue

            cell = self.grid[coord]
            if cell.soil not in spec.preferred_soil:
                continue

            # Place plant: replaces existing plant and resets age to 0
            cell.plant_index = spec.index
            cell.plant_age = 0
            cell.dead_matter = False
            cell.last_spread_tick = tick
            self.occupied_coords.add(coord)
            if coord in self.dead_matter_coords:
                self.dead_matter_coords.discard(coord)

            if spec.plant == "Oak Tree":
                self.tree_coords.add(coord)
            elif coord in self.tree_coords:
                self.tree_coords.discard(coord)

        # Fast path: if no occupied cells and no dead matter, early return
        if not self.occupied_coords and not self.dead_matter_coords:
            return

        # --- Phase 3: Recalculate Shade ---
        self._recalculate_shade()

        # --- Phase 4: Autonomous Spreading ---
        self._resolve_spreading(tick)

        # --- Phase 5: Shade Survival Check ---
        dead_from_shade = []
        for coord in list(self.occupied_coords):
            cell = self.grid[coord]
            if cell.is_shaded and cell.plant_index is not None:
                spec = self.loader.plants.get(cell.plant_index)
                if spec:
                    for w in spec.weaknesses:
                        if w.get("type") == "no_shade_survival":
                            cell.plant_index = None
                            cell.plant_age = 0
                            cell.dead_matter = True
                            dead_from_shade.append(coord)
                            break
        for coord in dead_from_shade:
            self.occupied_coords.discard(coord)
            self.tree_coords.discard(coord)
            self.dead_matter_coords.add(coord)

        # --- Phase 6: Nutrient Consumption & Regeneration ---
        starved_coords = []
        for coord in list(self.occupied_coords):
            cell = self.grid[coord]
            drain = 0.5 if cell.dead_matter else 1.0
            cell.nutrients -= drain
            if cell.nutrients <= 0.0:
                cell.nutrients = 0.0
                cell.plant_index = None
                cell.plant_age = 0
                cell.dead_matter = True
                starved_coords.append(coord)

        for coord in starved_coords:
            self.occupied_coords.discard(coord)
            self.tree_coords.discard(coord)
            self.dead_matter_coords.add(coord)

        # Regenerate nutrients on empty dead matter cells
        clean_dead_matter = []
        for coord in list(self.dead_matter_coords):
            if coord in self.occupied_coords:
                continue
            cell = self.grid[coord]
            cell.nutrients = min(100.0, cell.nutrients + 1.0)
            if cell.nutrients >= 100.0:
                cell.dead_matter = False
                clean_dead_matter.append(coord)
        for coord in clean_dead_matter:
            self.dead_matter_coords.discard(coord)

        # --- Phase 7: Plant Maturation & Aging ---
        for coord in self.occupied_coords:
            cell = self.grid[coord]
            cell.plant_age += 1

    def _recalculate_shade(self):
        # Reset shade on active cells
        for cell in self.grid.values():
            cell.is_shaded = False

        if not self.tree_coords:
            return

        for r, c in self.tree_coords:
            cell = self.grid.get((r, c))
            if cell and cell.plant_index == 12:
                spec = self.loader.plants.get(12)
                if spec and cell.plant_age >= spec.growth.time_to_maturity:
                    for dr, dc in get_shade_offsets(4):
                        target = (r + dr, c + dc)
                        if target in self.grid:
                            self.grid[target].is_shaded = True

    def _resolve_spreading(self, tick: int):
        spread_events: List[Tuple[Tuple[int, int], int]] = []

        for coord in list(self.occupied_coords):
            cell = self.grid[coord]
            if cell.plant_index is None:
                continue

            spec = self.loader.plants.get(cell.plant_index)
            if not spec:
                continue

            growth = spec.growth
            if cell.plant_age < growth.time_to_maturity:
                continue

            effective_spread_rate = growth.spread_rate
            for mod in growth.conditional_modifiers:
                if mod.get("condition") == f"season_{self.current_season.lower()}":
                    effective_spread_rate = mod.get("spread_rate", effective_spread_rate)

            # Animal effects on spread rate
            if "Nectaris" in self.active_animals and spec.role == "Pollinator-dependent":
                effective_spread_rate = max(1, int(effective_spread_rate / 1.5))
            if "Barkskips" in self.active_animals and spec.plant in ("Oak Tree", "Purple Canopy Tree"):
                effective_spread_rate = max(1, int(effective_spread_rate / 1.1))

            if self.current_season == "Winter":
                if any(w.get("type") == "no_winter_spread" for w in spec.weaknesses):
                    continue

            if cell.is_shaded:
                if any(w.get("type") == "no_shade_spread" for w in spec.weaknesses):
                    continue

            ticks_since_spread = tick - cell.last_spread_tick
            if ticks_since_spread >= effective_spread_rate:
                cell.last_spread_tick = tick
                r, c = coord
                offsets = get_spread_offsets(growth.spread_type, growth.spread_range)
                for dr, dc in offsets:
                    target_coord = (r + dr, c + dc)
                    if target_coord in self.grid:
                        target_cell = self.grid[target_coord]
                        if target_cell.soil in spec.preferred_soil:
                            if target_cell.is_shaded and any(
                                w.get("type") in ("no_shade_survival", "no_shade_spread") for w in spec.weaknesses
                            ):
                                continue
                            spread_events.append((target_coord, spec.index))

        for target_coord, p_idx in spread_events:
            target_cell = self.grid[target_coord]
            target_cell.plant_index = p_idx
            target_cell.plant_age = 0
            target_cell.last_spread_tick = tick
            self.occupied_coords.add(target_coord)
            if p_idx == 12:
                self.tree_coords.add(target_coord)
            elif target_coord in self.tree_coords:
                self.tree_coords.discard(target_coord)

    def _update_animals_and_unlocks(self):
        counts: Dict[str, int] = {}
        coverages: Dict[str, float] = {}
        alive_total = len(self.occupied_coords)

        for coord in self.occupied_coords:
            cell = self.grid[coord]
            if cell.plant_index is not None:
                spec = self.loader.plants.get(cell.plant_index)
                if spec:
                    counts[spec.plant] = counts.get(spec.plant, 0) + 1

        total_cells = len(self.grid)
        for plant_name, cnt in counts.items():
            coverages[plant_name] = cnt / total_cells if total_cells > 0 else 0.0

        dead_matter_count = len(self.dead_matter_coords)
        context = {
            "plant_counts": counts,
            "plant_coverages": coverages,
            "feature_counts": {"dead_matter": dead_matter_count},
            "total_alive": alive_total
        }

        # Update animals
        if self.animals_enabled:
            current_animals = set()
            for animal in self.loader.animals:
                if check_animal_requirements(animal.get("requirements", {}), context, self.loader.classifications):
                    current_animals.add(animal["name"])
            self.active_animals = current_animals

        evaluator = UnlockTreeEvaluator(
            unlocked_species=self.unlocked_species,
            active_animals=self.active_animals,
            active_events=self.active_events
        )

        for item in self.loader.unlock_conditions:
            p_name = item.get("plant", "")
            if p_name not in self.unlocked_species:
                if evaluator.evaluate(item.get("unlock", {}), context):
                    self.unlocked_species.add(p_name)

    def calculate_score(self) -> ScoreResult:
        species_counts: Dict[int, int] = {}
        total_alive = 0
        longevity_sum = 0.0

        T = self.total_ticks
        k = 1.0
        alpha = 1.0
        c_max = len(self.habitable_coords)

        for coord in self.occupied_coords:
            cell = self.grid[coord]
            if cell.plant_index is not None:
                idx = cell.plant_index
                species_counts[idx] = species_counts.get(idx, 0) + 1
                total_alive += 1
                l_ij = cell.plant_age
                longevity_sum += (l_ij / T) ** k

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

        K = 5
        entropy = 0.0
        for idx, count in species_counts.items():
            p_i = count / total_alive
            if p_i > 0:
                entropy -= p_i * (math.log(p_i) / math.log(K))

        coverage_ratio = min(1.0, total_alive / c_max)
        sample_factor = coverage_ratio ** alpha
        main_score = entropy * sample_factor
        longevity_score = longevity_sum / c_max
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
