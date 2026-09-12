import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.loader import ResourceLoader
from core.engine import SimulationEngine
from strategies.level3_expert import Level3ExpertStrategy

class TestLevel3Engine(unittest.TestCase):
    def setUp(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.loader = ResourceLoader(base_dir)
        lvl3_path = os.path.join(base_dir, "3.json")
        self.config = self.loader.load_level(lvl3_path)
        self.engine = SimulationEngine(self.config, self.loader)

    def test_grid_initialization(self):
        self.assertEqual(self.config.rows, 150)
        self.assertEqual(self.config.cols, 150)
        self.assertEqual(self.config.ticks, 800)
        self.assertEqual(len(self.config.cells), 4921)
        self.assertEqual(len(self.engine.habitable_coords), 4280)

    def test_strategy_constraints(self):
        strategy = Level3ExpertStrategy()
        submission = strategy.generate_submission(self.config, self.loader)

        # Check tick constraints
        for entry in submission.actions:
            self.assertGreaterEqual(entry.tick, 0)
            self.assertLess(entry.tick, 800)
            self.assertLessEqual(len(entry.plants), 20)

            for plant in entry.plants:
                coord = (plant.row, plant.col)
                self.assertIn(coord, self.config.cells)
                cell = self.config.cells[coord]
                spec = self.loader.plants[plant.plant_index]
                self.assertIn(cell.soil, spec.preferred_soil)

    def test_scoring_performance(self):
        strategy = Level3ExpertStrategy()
        submission = strategy.generate_submission(self.config, self.loader)
        result = self.engine.run(submission)

        self.assertGreater(result.alive_count, 2500)
        self.assertGreater(result.entropy, 0.50)
        self.assertGreater(result.leaderboard_score, 50_000_000)

if __name__ == "__main__":
    unittest.main()

