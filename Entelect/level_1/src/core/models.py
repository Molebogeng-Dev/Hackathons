from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set, Any

@dataclass
class GrowthSpec:
    time_to_maturity: int
    spread_rate: int
    spread_mechanism: str
    spread_type: str
    spread_range: int
    root_type: str
    invasiveness_rank: int
    conditional_modifiers: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class PlantSpec:
    plant: str
    index: int
    growth: GrowthSpec
    preferred_soil: List[int]
    weaknesses: List[Dict[str, Any]] = field(default_factory=list)
    special: List[Dict[str, Any]] = field(default_factory=list)
    role: str = ""

@dataclass
class CellState:
    row: int
    col: int
    terrain: int
    soil: int
    nutrients: float = 100.0
    dead_matter: bool = False
    plant_index: Optional[int] = None
    plant_age: int = 0
    is_shaded: bool = False
    last_spread_tick: int = -1

    def copy(self) -> CellState:
        return CellState(
            row=self.row,
            col=self.col,
            terrain=self.terrain,
            soil=self.soil,
            nutrients=self.nutrients,
            dead_matter=self.dead_matter,
            plant_index=self.plant_index,
            plant_age=self.plant_age,
            is_shaded=self.is_shaded,
            last_spread_tick=self.last_spread_tick
        )

@dataclass
class PlantAction:
    plant_index: int
    row: int
    col: int

    def to_dict(self, mode: str = "DUAL") -> Dict[str, int]:
        if mode == "DUAL":
            return {
                "plant_index": self.plant_index,
                "index": self.plant_index,
                "row": self.row,
                "col": self.col
            }
        elif mode == "PLANT_INDEX":
            return {
                "plant_index": self.plant_index,
                "row": self.row,
                "col": self.col
            }
        elif mode == "INDEX":
            return {
                "index": self.plant_index,
                "row": self.row,
                "col": self.col
            }
        else:
            raise ValueError(f"Unknown serialization mode: {mode}")

@dataclass
class TickEntry:
    tick: int
    plants: List[PlantAction] = field(default_factory=list)

    def to_dict(self, mode: str = "DUAL") -> Dict[str, Any]:
        return {
            "tick": self.tick,
            "plants": [p.to_dict(mode) for p in self.plants]
        }

@dataclass
class Submission:
    actions: List[TickEntry] = field(default_factory=list)

    def to_dict(self, mode: str = "DUAL") -> Dict[str, Any]:
        return {
            "actions": [a.to_dict(mode) for a in sorted(self.actions, key=lambda x: x.tick)]
        }

@dataclass
class LevelConfig:
    rows: int
    cols: int
    ticks: int
    animals_enabled: bool
    cells: Dict[Tuple[int, int], CellState]
    commands: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class ScoreResult:
    alive_count: int
    max_cells: int
    entropy: float
    main_score: float
    longevity_score: float
    final_score: float
    leaderboard_score: int
    species_distribution: Dict[int, int]

