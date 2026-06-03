from abc import ABC, abstractmethod
import pandas as pd


class Extractor(ABC):
    def __init__(self):
        self._compile_patterns()

    @abstractmethod
    def _compile_patterns(self):
        pass

    @abstractmethod
    def extract(self, content: str) -> pd.DataFrame:
        pass

    def validate_data(self, df: pd.DataFrame) -> bool:
        return not df.empty and df.shape[1] > 0
