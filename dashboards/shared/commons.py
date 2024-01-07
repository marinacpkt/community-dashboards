
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple


def get_ds_name(datasource) -> str:
    if isinstance(datasource, Dict):
        return datasource["uid"]
    else:
        return datasource


class DashboardTransformError(Exception):
    """Exception raised for errors in the division."""

    def __init__(self, message):
        self.message = message


class AbstractDashboardEditor(ABC):

    @staticmethod
    @abstractmethod
    def from_file(file: str, key: Optional[str] = None) -> Optional[List[Tuple[Dict, Optional[str]]]]:
        raise NotImplementedError
    