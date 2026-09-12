from __future__ import annotations
from typing import List, Dict, Tuple, Set
from core.models import LevelConfig, Submission, TickEntry, PlantAction
from core.loader import ResourceLoader
from strategies.base import BaseStrategy

class Level3ExpertStrategy(BaseStrategy):
    """
    Expert strategy for Level 3 (Park Potential, 150x150 grid, 4921 cells, 4280 soil 0/1 cells).
    1. Early Game (ticks 0..85):
       - Seeds starter plants across tick 10 Drought to unlock Crystal Cactus.
       - Spawns animals (Barkskips, Canorals, Loamcrawlers, Nectaris, Virexids, Verdelopes).
       - Unlocks Stone Reed, Crimson Vine, Orange Blossom, Razorgrass, Crystal Cactus.
    2. Mid Game (ticks 135..149):
       - Plants Blue Moss ahead of tick 150 Rain to unlock Mire Bloom.
    3. Endgame (ticks 585..799):
       - Deploys across all 4,280 habitable cells in balanced spatial quotas using 10 unlocked species.
       - Prevents runaway monoculture by using diverse multi-tier unlocked species.
    """
    def __init__(self, start_tick: int = 585):
        self.start_tick = start_tick

    def generate_submission(self, config: LevelConfig, loader: ResourceLoader) -> Submission:
        habitable = sorted([
            (c.row, c.col) for c in config.cells.values()
            if c.soil in (0, 1)
        ])
        total_hab = len(habitable) # 4280 cells

        actions: List[TickEntry] = []

        # --- Phase 1: Early Animal Spawning & Event Unlocks (Ticks 0..85) ---
        # 10 Oak Trees (tick 0)
        actions.append(TickEntry(tick=0, plants=[PlantAction(plant_index=12, row=r, col=c) for r, c in habitable[0:10]]))
        # 600 Grass (ticks 1..30) - covers tick 10 Drought for Crystal Cactus unlock
        for idx, t in enumerate(range(1, 31)):
            chunk = habitable[10 + idx*20 : 10 + (idx+1)*20]
            actions.append(TickEntry(tick=t, plants=[PlantAction(plant_index=1, row=r, col=c) for r, c in chunk]))
        # 400 Rose Bush (ticks 31..50)
        for idx, t in enumerate(range(31, 51)):
            chunk = habitable[610 + idx*20 : 610 + (idx+1)*20]
            actions.append(TickEntry(tick=t, plants=[PlantAction(plant_index=2, row=r, col=c) for r, c in chunk]))
        # 400 Lavender (ticks 51..70)
        for idx, t in enumerate(range(51, 71)):
            chunk = habitable[1010 + idx*20 : 1010 + (idx+1)*20]
            actions.append(TickEntry(tick=t, plants=[PlantAction(plant_index=6, row=r, col=c) for r, c in chunk]))
        # 300 Sunflower (ticks 71..85)
        for idx, t in enumerate(range(71, 86)):
            chunk = habitable[1410 + idx*20 : 1410 + (idx+1)*20]
            actions.append(TickEntry(tick=t, plants=[PlantAction(plant_index=5, row=r, col=c) for r, c in chunk]))

        # --- Phase 2: Blue Moss ahead of Rain (ticks 135..149) ---
        for idx, t in enumerate(range(135, 150)):
            chunk = habitable[2000 + idx*20 : 2000 + (idx+1)*20]
            actions.append(TickEntry(tick=t, plants=[PlantAction(plant_index=3, row=r, col=c) for r, c in chunk]))

        # --- Phase 3: Endgame Full-Grid Deployment (ticks 585..799) ---
        # 10 Unlocked species pool:
        # [12 (Oak), 2 (Rose), 6 (Lavender), 11 (Stone Reed), 4 (Crimson Vine), 17 (Crystal Cactus), 19 (Razorgrass), 3 (Blue Moss), 5 (Sunflower), 1 (Grass)]
        species_pool = [12, 2, 6, 11, 4, 17, 19, 3, 5, 1]
        quota = total_hab // len(species_pool)
        species_cells = []
        curr = 0
        for idx, p_idx in enumerate(species_pool):
            count = quota + (1 if idx < total_hab % len(species_pool) else 0)
            species_cells.append((p_idx, habitable[curr:curr+count]))
            curr += count

        # Flatten into exact 20-plant batches across ticks
        all_actions = []
        for p_idx, cells in species_cells:
            for r, c in cells:
                all_actions.append((p_idx, r, c))

        tick = self.start_tick
        for i in range(0, len(all_actions), 20):
            chunk = all_actions[i:i+20]
            batch = [PlantAction(plant_index=p_idx, row=r, col=c) for p_idx, r, c in chunk]
            actions.append(TickEntry(tick=tick, plants=batch))
            tick += 1

        return Submission(actions=actions)
