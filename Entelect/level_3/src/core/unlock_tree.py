from __future__ import annotations
from typing import Dict, Any, Set, List
import operator

OPS = {
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
    "==": operator.eq,
    "=": operator.eq
}

class UnlockTreeEvaluator:
    def __init__(self, unlocked_species: Set[str], active_animals: Set[str], active_events: Set[str]):
        self.unlocked_species = set(unlocked_species)
        self.active_animals = set(active_animals)
        self.active_events = set(active_events)

    def evaluate(self, node: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """
        Recursively evaluates an unlock condition node.
        context should contain:
          - 'plant_counts': Dict[str, int]
          - 'plant_coverages': Dict[str, float]
          - 'feature_counts': Dict[str, int]
        """
        if "op" in node:
            op = node["op"].upper()
            if op == "AND":
                return all(self.evaluate(child, context) for child in node.get("children", []))
            elif op == "OR":
                return any(self.evaluate(child, context) for child in node.get("children", []))
            elif op == "NOT":
                return not self.evaluate(node.get("child", {}), context)
            else:
                return False

        c_type = node.get("type", "")
        op_func = OPS.get(node.get("operator", ">="), operator.ge)
        target_val = node.get("value", 0)

        if c_type == "species_present":
            species = node.get("species", "")
            return species in self.active_animals or species in self.unlocked_species

        elif c_type == "species_absent":
            species = node.get("species", "")
            return species not in self.active_animals and species not in self.unlocked_species

        elif c_type == "coverage":
            plant = node.get("plant", "")
            coverages = context.get("plant_coverages", {})
            return op_func(coverages.get(plant, 0.0), target_val)

        elif c_type == "count":
            plant = node.get("plant", "")
            counts = context.get("plant_counts", {})
            return op_func(counts.get(plant, 0), target_val)

        elif c_type == "event":
            event = node.get("event", "")
            return event in self.active_events

        elif c_type == "feature_count":
            feat = node.get("feature", "")
            f_counts = context.get("feature_counts", {})
            return op_func(f_counts.get(feat, 0), target_val)

        return False

