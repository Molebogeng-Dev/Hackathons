from __future__ import annotations
from typing import List, Dict, Tuple, Set
from core.models import LevelConfig, Submission, TickEntry, PlantAction
from core.loader import ResourceLoader
from strategies.base import BaseStrategy

class Level2ExpertStrategy(BaseStrategy):
    """
    Expert strategy for Level 2 (Garden Growth Study):
    1. Early Game (ticks 0..35):
       - Plants starter species to satisfy animal thresholds (Barkskips, Canorals, Loamcrawlers, Nectaris, Solwings, Virexids, Verdelopes).
       - Unlocks Blue Moss, Crimson Vine, Orange Blossom, Stone Reed, Razorgrass.
    2. Mid Game (ticks 230..248):
       - Plants Blue Moss to exceed 0.05 coverage before tick 250 Rain event.
       - Unlocks Mire Bloom (which can grow in Clay!).
    3. Endgame (ticks 440..499):
       - Populates all 184 clay cells with Mire Bloom.
       - Populates all 926 habitable dirt/mud cells with a balanced distribution of 10 unlocked species.
       - Maximizes diversity H across 11 species, avoiding monocultures.
    """
    def __init__(self, start_tick: int = 440):
        self.start_tick = start_tick

    def generate_submission(self, config: LevelConfig, loader: ResourceLoader) -> Submission:
        habitable = sorted([
            (c.row, c.col) for c in config.cells.values()
            if c.soil in (0, 1)
        ])
        clay_cells = sorted([
            (c.row, c.col) for c in config.cells.values()
            if c.soil == 2
        ])
        total_hab = len(habitable)
        total_clay = len(clay_cells)

        actions: List[TickEntry] = []

        # --- Phase 1: Early Animal Spawning & Unlocking (Ticks 0..35) ---
        # 10 Oak Trees (Barkskips & Canorals)
        actions.append(TickEntry(tick=0, plants=[PlantAction(plant_index=12, row=r, col=c) for r, c in habitable[0:10]]))
        # 140 Rose Bush (Nectaris & Solwings)
        for idx, t in enumerate(range(1, 8)):
            chunk = habitable[10 + idx*20 : 10 + (idx+1)*20]
            actions.append(TickEntry(tick=t, plants=[PlantAction(plant_index=2, row=r, col=c) for r, c in chunk]))
        # 140 Lavender (Nectaris & Virexids)
        for idx, t in enumerate(range(8, 15)):
            chunk = habitable[150 + idx*20 : 150 + (idx+1)*20]
            actions.append(TickEntry(tick=t, plants=[PlantAction(plant_index=6, row=r, col=c) for r, c in chunk]))
        # 280 Grass (Loamcrawlers & Verdelopes)
        for idx, t in enumerate(range(15, 29)):
            chunk = habitable[290 + idx*20 : 290 + (idx+1)*20]
            actions.append(TickEntry(tick=t, plants=[PlantAction(plant_index=1, row=r, col=c) for r, c in chunk]))
        # 210 Sunflower (Solwings)
        for idx, t in enumerate(range(29, 40)):
            chunk = habitable[570 + idx*20 : min(total_hab, 570 + (idx+1)*20)]
            if chunk:
                actions.append(TickEntry(tick=t, plants=[PlantAction(plant_index=5, row=r, col=c) for r, c in chunk]))

        # --- Phase 2: Blue Moss for Rain Mire Bloom Unlock (Ticks 230..247) ---
        for idx, t in enumerate(range(230, 248)):
            chunk = habitable[idx*20 : (idx+1)*20]
            actions.append(TickEntry(tick=t, plants=[PlantAction(plant_index=3, row=r, col=c) for r, c in chunk]))

        # --- Phase 3: Endgame Balanced Deployment (Ticks 440..499) ---
        tick = self.start_tick
        # 1. Populate Clay with Mire Bloom (18)
        for i in range(0, total_clay, 20):
            chunk = clay_cells[i:i+20]
            actions.append(TickEntry(tick=tick, plants=[PlantAction(plant_index=18, row=r, col=c) for r, c in chunk]))
            tick += 1

        # 2. Balanced 10 Unlocked Species across habitable soil
        species_pool = [12, 2, 6, 11, 4, 7, 3, 19, 5, 1]
        quota = total_hab // len(species_pool)
        species_cells = []
        curr = 0
        for idx, p_idx in enumerate(species_pool):
            count = quota + (1 if idx < total_hab % len(species_pool) else 0)
            species_cells.append((p_idx, habitable[curr:curr+count]))
            curr += count

        for p_idx, cells in species_cells:
            for i in range(0, len(cells), 20):
                batch = [PlantAction(plant_index=p_idx, row=r, col=c) for r, c in cells[i:i+20]]
                actions.append(TickEntry(tick=tick, plants=batch))
                tick += 1

        return Submission(actions=actions)
