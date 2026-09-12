from __future__ import annotations
from abc import ABC, abstractmethod
from core.models import LevelConfig, Submission
from core.loader import ResourceLoader

class BaseStrategy(ABC):
    @abstractmethod
    def generate_submission(self, config: LevelConfig, loader: ResourceLoader) -> Submission:
        """
        Given the level configuration and resource catalogues,
        returns a valid Submission containing scheduled planting actions.
        """
        pass
