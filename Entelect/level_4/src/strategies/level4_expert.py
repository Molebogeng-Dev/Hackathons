from __future__ import annotations
from typing import List, Dict, Tuple, Set, Optional
from core.models import LevelConfig, Submission, PlantAction, TickEntry
from core.loader import ResourceLoader
from strategies.base import BaseStrategy

class Level4ExpertStrategy(BaseStrategy):
    """
    Expert strategy for Level 4 (Forest, 200x300 grid, 6413 cells, 5406 habitable soil 0/1 cells).
    1. Early Game (ticks 0..85):
       - Seeds starter plants across tick 50 Rain and tick 280 Drought to trigger unlocks.
       - Spawns Barkskips, Canorals, Loamcrawlers, Nectaris, Virexids, Verdelopes.
       - Unlocks Stone Reed, Crystal Cactus, Razorgrass, Glowcap Fungus.
    2. Endgame (ticks 530..799):
       - Deploys across all 5,406 habitable cells in balanced spatial quotas using unlocked species.
       - Prevents Oak Tree and Sunflower extinction by scheduling distinct multi-tier species.
    """
    def __init__(self, config: Optional[LevelConfig] = None, loader: Optional[ResourceLoader] = None, start_tick: int = 529):
        super().__init__()
        self.config = config
        self.loader = loader
        self.start_tick = start_tick

    def solve(self) -> Submission:
        if self.config is None:
            raise ValueError("Config not provided to Level4ExpertStrategy")
        return self.generate_submission(self.config, self.loader)

    def generate_submission(self, config: LevelConfig, loader: Optional[ResourceLoader] = None) -> Submission:
        habitable = sorted([
            (c.row, c.col) for c in config.cells.values()
            if c.soil in (0, 1)
        ])
        total_hab = len(habitable) # 5406 cells

        actions: List[TickEntry] = []

        # --- Phase 1: Early Animal Spawning & Unlocking (Ticks 0..85) ---
        # 10 Oak Trees (tick 0)
        actions.append(TickEntry(tick=0, plants=[PlantAction(plant_index=12, row=r, col=c) for r, c in habitable[0:10]]))
        # 600 Grass (ticks 1..30)
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

        # --- Phase 2: Endgame Deployment Across Full Habitable Grid (Ticks 530..799) ---
        # Unlocked species: [12 (Oak), 2 (Rose), 6 (Lavender), 11 (Stone Reed), 17 (Crystal Cactus), 19 (Razorgrass), 9 (Glowcap), 5 (Sunflower), 1 (Grass)]
        species_pool = [12, 2, 6, 11, 17, 19, 9, 5, 1]
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
