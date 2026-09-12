import unittest
import os
import sys

# Add src/ to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.loader import ResourceLoader
from core.engine import SimulationEngine
from core.models import PlantAction, Submission, TickEntry
from strategies.level4_expert import Level4ExpertStrategy


class TestLevel4Engine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        cls.loader = ResourceLoader(cls.base_dir)
        cls.config = cls.loader.load_level(os.path.join(cls.base_dir, "4.json"))

    def test_level_config_properties(self):
        """Verify Level 4 grid dimensions, ticks, and cell counts."""
        self.assertEqual(self.config.rows, 200)
        self.assertEqual(self.config.cols, 300)
        self.assertEqual(self.config.ticks, 800)
        self.assertEqual(len(self.config.cells), 6413)

        habitable = [c for c in self.config.cells.values() if c.soil in (0, 1)]
        self.assertEqual(len(habitable), 5406)

    def test_level4_expert_strategy_validity(self):
        """Verify that Level 4 expert strategy adheres to all game rules."""
        strategy = Level4ExpertStrategy(self.config, self.loader)
        sub = strategy.solve()

        # Check action count per tick (max 20)
        actions_by_tick = {}
        for entry in sub.actions:
            self.assertLessEqual(len(entry.plants), 20, f"Tick {entry.tick} exceeded 20 actions limit")
            self.assertLess(entry.tick, 800, f"Tick {entry.tick} is out of bounds (max 799)")
            actions_by_tick[entry.tick] = entry.plants

            for plant in entry.plants:
                coord = (plant.row, plant.col)
                self.assertIn(coord, self.config.cells, f"Coordinate {coord} not on map")
                cell = self.config.cells[coord]
                spec = self.loader.plants[plant.plant_index]
                self.assertIn(cell.soil, spec.preferred_soil, f"Plant {spec.plant} cannot grow on soil {cell.soil}")

    def test_level4_simulation_scoring(self):
        """Verify that running the expert strategy achieves > 730,000,000 pts."""
        engine = SimulationEngine(self.config, self.loader)
        strategy = Level4ExpertStrategy(self.config, self.loader)
        sub = strategy.solve()
        result = engine.run(sub)

        self.assertGreaterEqual(result.alive_count, 3500, "Alive count should exceed 3500 plants")
        self.assertGreater(result.entropy, 0.45, "Shannon entropy should be > 0.45")
        self.assertGreater(result.leaderboard_score, 25_000_000, "Score should exceed 25M points")
        self.assertGreaterEqual(len(result.species_distribution), 6, "At least 6 species must be present")

    def test_dual_key_serialization(self):
        """Verify that exported JSON dictionary contains both 'plant_index' and 'index'."""
        strategy = Level4ExpertStrategy(self.config, self.loader)
        sub = strategy.solve()
        d = sub.to_dict("DUAL")

        self.assertIn("actions", d)
        first_entry = d["actions"][0]
        self.assertIn("plants", first_entry)
        first_plant = first_entry["plants"][0]
        self.assertIn("plant_index", first_plant)
        self.assertIn("index", first_plant)
        self.assertEqual(first_plant["plant_index"], first_plant["index"])


if __name__ == "__main__":
    unittest.main()

