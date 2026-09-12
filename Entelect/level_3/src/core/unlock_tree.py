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

class AnimalEvaluator:
    def __init__(self, animals: List[Dict[str, Any]], classifications: Dict[str, List[str]]):
        self.animals = animals
        self.classifications = classifications

    def _resolve_species_list(self, items: List[str]) -> List[str]:
        species = []
        for it in items:
            if it in self.classifications:
                species.extend(self.classifications[it])
            else:
                species.append(it)
        return list(set(species))

    def evaluate_all(self, context: Dict[str, Any]) -> Set[str]:
        counts = context.get("plant_counts", {})
        total_cells = context.get("total_cells", 1)
        total_alive = context.get("total_alive", 0)

        active = set()
        for a in self.animals:
            req = a.get("requirements", {})
            if self._eval_req(req, counts, total_cells, total_alive):
                active.add(a.get("name", a.get("id", "")))
        return active

    def _eval_req(self, req: Dict[str, Any], counts: Dict[str, int], total_cells: int, total_alive: int) -> bool:
        rtype = req.get("type", "").upper()
        if rtype == "OR":
            return any(self._eval_req(c, counts, total_cells, total_alive) for c in req.get("conditions", []))
        elif rtype == "AND":
            return all(self._eval_req(c, counts, total_cells, total_alive) for c in req.get("conditions", []))

        cond_type = req.get("type", "")
        op = OPS.get(req.get("operator", ">="), operator.ge)
        thresh = req.get("threshold", 0)

        if cond_type == "coverage":
            species = req.get("species", [])
            total_cnt = sum(counts.get(s, 0) for s in species)
            cov = total_cnt / total_cells if total_cells > 0 else 0.0
            return op(cov, thresh)

        elif cond_type == "group_coverage":
            group = req.get("species_group", [])
            resolved = self._resolve_species_list(group)
            total_cnt = sum(counts.get(s, 0) for s in resolved)
            cov = total_cnt / total_cells if total_cells > 0 else 0.0
            return op(cov, thresh)

        elif cond_type == "count":
            if "species" in req:
                cnt = counts.get(req["species"], 0)
            elif "species_group" in req:
                resolved = self._resolve_species_list(req["species_group"])
                cnt = sum(counts.get(s, 0) for s in resolved)
            else:
                cnt = 0
            return op(cnt, thresh)

        elif cond_type == "dominance":
            if total_alive <= 0:
                return False
            max_cnt = max(counts.values()) if counts else 0
            return (max_cnt / total_alive) >= thresh

        return False

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
