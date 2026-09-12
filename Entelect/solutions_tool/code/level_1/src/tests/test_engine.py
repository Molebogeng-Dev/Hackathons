import unittest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.models import LevelConfig, CellState, PlantAction, TickEntry, Submission
from core.loader import ResourceLoader
from core.engine import SimulationEngine

class TestSimulationEngine(unittest.TestCase):
    def setUp(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        self.loader = ResourceLoader(base_dir=base_dir)
        # Create a small 10x10 mock grid
        cells = {}
        for r in range(10):
            for c in range(10):
                cells[(r, c)] = CellState(row=r, col=c, terrain=0, soil=0, nutrients=100.0)
        self.config = LevelConfig(
            rows=10, cols=10, ticks=150, animals_enabled=False, cells=cells
        )
        self.engine = SimulationEngine(self.config, self.loader)

    def test_nutrient_normal_depletion(self):
        # Plant Grass (index 1) at (0, 0) on tick 0
        actions = [TickEntry(tick=0, plants=[PlantAction(plant_index=1, row=0, col=0)])]

        # Run 99 ticks: plant should still be alive, nutrients at 1.0
        for tick in range(99):
            self.engine.current_tick = tick
            player_acts = actions[0].plants if tick == 0 else []
            self.engine.step(player_acts)

        cell = self.engine.grid[(0, 0)]
        self.assertEqual(cell.plant_index, 1)
        self.assertAlmostEqual(cell.nutrients, 1.0)
        self.assertFalse(cell.dead_matter)

        # Tick 99 (100th step): nutrients reach 0, plant dies
        self.engine.current_tick = 99
        self.engine.step([])
        cell = self.engine.grid[(0, 0)]
        self.assertIsNone(cell.plant_index)
        self.assertTrue(cell.dead_matter)
        self.assertAlmostEqual(cell.nutrients, 0.0)

    def test_dead_matter_regeneration_and_half_depletion(self):
        # Set up a cell with dead matter and 0 nutrients
        cell = self.engine.grid[(0, 0)]
        cell.dead_matter = True
        cell.nutrients = 0.0

        # Step 50 ticks empty: nutrients should regenerate to 50.0
        for tick in range(50):
            self.engine.current_tick = tick
            self.engine.step([])
        self.assertAlmostEqual(cell.nutrients, 50.0)

        # Now plant Grass on this dead-matter cell at tick 50
        self.engine.current_tick = 50
        self.engine.step([PlantAction(plant_index=1, row=0, col=0)])

        # At tick 50, Phase 6 consumes 0.5 -> 49.5
        # Step 10 more ticks (51..60): 10 * 0.5 = 5.0 consumed, remaining is 44.5
        for tick in range(51, 61):
            self.engine.current_tick = tick
            self.engine.step([])
        self.assertAlmostEqual(cell.nutrients, 44.5)

    def test_oak_tree_shade_kills_grass(self):
        # Plant Oak Tree (index 12) at (5, 5) on tick 0
        self.engine.step([PlantAction(plant_index=12, row=5, col=5)])

        # Step until Oak Tree matures (reaches age 20 at tick 19)
        for tick in range(1, 21):
            self.engine.current_tick = tick
            self.engine.step([])

        # Oak Tree is now mature and casting shade.
        # Now place Grass at (5, 6) which is within shade radius 4
        self.engine.current_tick = 21
        self.engine.step([PlantAction(plant_index=1, row=5, col=6)])

        grass_cell = self.engine.grid[(5, 6)]
        # Grass must have died due to no_shade_survival
        self.assertIsNone(grass_cell.plant_index)
        self.assertTrue(grass_cell.is_shaded)
        self.assertTrue(grass_cell.dead_matter)

if __name__ == '__main__':
    unittest.main()

