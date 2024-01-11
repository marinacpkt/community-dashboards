from typing import  Dict, List, Optional, Tuple
from dashboards.processor.dashboard_processor import AbstractProcessor
from dashboards.editor.dashboard_editor import DashboardTransformError
from dashboards.shared.constants import KEY_UID

class DashboardTransformConfigError(Exception):
    """Exception raised for errors in the division."""

    def __init__(self, message):
        self.message = message
class DashboardGenerator(AbstractProcessor):

    def _traverse_update(self, element: Dict|List) -> None:
        """Traversing the passed in dashboard recursively and update as needed: root is dashboard root.
        """
        if isinstance(element, Dict):
            # TODO: process Dict item
            # 1...
            # 2...
            for value in element.values():
                if isinstance(value, Dict|List):
                    self._traverse_update(value)
                else:   # value as: str|bool|int|float - owned by a dictionary
                    # TODO: process
                    # print(f'{key} - {value}')
                    pass
        elif isinstance(element, list):
            # TODO: process List item
            # 1...
            # 2...
            for item in element:
                if isinstance(item, Dict) or isinstance(item, List):
                    self._traverse_update(item)
                else:   # item as: str|bool|int|float - owned by a list
                    # TODO: process
                    print(f'{element} - {item}')

    
    def process_dashboard(self, dashboard_schema: Dict, key = None) -> Optional[List[Tuple[Dict, Optional[str]]]]:
        if not dashboard_schema: 
            raise DashboardTransformError('A dashboard schema is required to create a dashboard.')
        # convert
        converted_dashboards: List[Tuple[Dict, Optional[str]]] = list()
        # TODO: create dashboard fro schema
        new_dashboard: Dict = {}
        converted_dashboards.append((new_dashboard, new_dashboard[KEY_UID]))
        return converted_dashboards