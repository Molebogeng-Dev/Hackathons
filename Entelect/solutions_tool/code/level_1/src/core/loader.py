from __future__ import annotations
import json
import os
from typing import Dict, Any, Tuple, List, Optional
from .models import LevelConfig, CellState, PlantSpec, GrowthSpec

def find_resource_file(filename: str, search_dirs: List[str]) -> str:
    for d in search_dirs:
        candidate = os.path.join(d, filename)
        if os.path.exists(candidate):
            return os.path.abspath(candidate)
    return filename

class ResourceLoader:
    def __init__(self, base_dir: Optional[str] = None):
        # Auto-detect base directory if not given or invalid
        candidates = [
            base_dir,
            "Entelect",
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."),
            ".",
        ]
        self.base_dir = "."
        for c in candidates:
            if c and os.path.exists(c) and (
                os.path.exists(os.path.join(c, "additional-resources")) or
                os.path.exists(os.path.join(c, "1.json"))
            ):
                self.base_dir = os.path.abspath(c)
                break

        # Locate additional-resources directory
        res_candidates = [
            os.path.join(self.base_dir, "additional-resources"),
            "additional-resources",
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "additional-resources"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "additional-resources"),
        ]
        self.resources_dir = self.base_dir
        for r in res_candidates:
            if os.path.exists(r):
                self.resources_dir = os.path.abspath(r)
                break

        self.plants: Dict[int, PlantSpec] = {}
        self.plants_by_name: Dict[str, PlantSpec] = {}
        self.animals: List[Dict[str, Any]] = []
        self.classifications: Dict[str, List[str]] = {}
        self.unlock_conditions: List[Dict[str, Any]] = []

        self._load_additional_resources()

    def _load_additional_resources(self):
        # Load plants
        plants_path = os.path.join(self.resources_dir, "plant_dataset.json")
        if os.path.exists(plants_path):
            with open(plants_path, "r") as f:
                data = json.load(f)
                for item in data:
                    g_data = item.get("growth", {})
                    growth = GrowthSpec(
                        time_to_maturity=g_data.get("time_to_maturity", 1),
                        spread_rate=g_data.get("spread_rate", 1),
                        spread_mechanism=g_data.get("spread_mechanism", ""),
                        spread_type=g_data.get("spread_type", "VonNeumann"),
                        spread_range=g_data.get("spread_range", 1),
                        root_type=g_data.get("root_type", "None"),
                        invasiveness_rank=g_data.get("invasiveness_rank", 1),
                        conditional_modifiers=g_data.get("conditional_modifiers", [])
                    )
                    rules = item.get("rules", {})
                    spec = PlantSpec(
                        plant=item.get("plant", ""),
                        index=item.get("index", 0),
                        growth=growth,
                        preferred_soil=item.get("preferred_soil", []),
                        weaknesses=rules.get("weaknesses", []),
                        special=rules.get("special", []),
                        role=item.get("role", "")
                    )
                    self.plants[spec.index] = spec
                    self.plants_by_name[spec.plant] = spec

        # Load animals
        animals_path = os.path.join(self.resources_dir, "animals.json")
        if os.path.exists(animals_path):
            with open(animals_path, "r") as f:
                self.animals = json.load(f)

        # Load classifications
        class_path = os.path.join(self.resources_dir, "classifications.json")
        if os.path.exists(class_path):
            with open(class_path, "r") as f:
                self.classifications = json.load(f)

        # Load unlock conditions
        unlock_path = os.path.join(self.resources_dir, "plant_unlock_conditions.json")
        if os.path.exists(unlock_path):
            with open(unlock_path, "r") as f:
                self.unlock_conditions = json.load(f)

    def load_level(self, level_file_path: str) -> LevelConfig:
        if not os.path.exists(level_file_path):
            candidates = [
                os.path.join(self.base_dir, level_file_path),
                os.path.join(self.base_dir, os.path.basename(level_file_path)),
                os.path.basename(level_file_path),
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", level_file_path),
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", os.path.basename(level_file_path)),
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", level_file_path),
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", os.path.basename(level_file_path)),
            ]
            for c in candidates:
                if os.path.exists(c):
                    level_file_path = os.path.abspath(c)
                    break

        with open(level_file_path, "r") as f:
            data = json.load(f)

        cells: Dict[Tuple[int, int], CellState] = {}
        for c in data.get("cells", []):
            r = c["row"]
            col = c["col"]
            cells[(r, col)] = CellState(
                row=r,
                col=col,
                terrain=c.get("terrain", 0),
                soil=c.get("soil", 0),
                nutrients=100.0,
                dead_matter=False,
                plant_index=None,
                plant_age=0,
                is_shaded=False,
                last_spread_tick=-1
            )

        return LevelConfig(
            rows=data.get("rows", 50),
            cols=data.get("cols", 50),
            ticks=data.get("ticks", 500),
            animals_enabled=data.get("animals_enabled", False),
            cells=cells,
            commands=data.get("commands", [])
        )

