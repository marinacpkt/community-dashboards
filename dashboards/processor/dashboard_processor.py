import json
from typing import  Dict, List, Optional, Tuple
from abc import ABC, abstractmethod
from dashboards.editor.dashboard_editor import DashboardTransformError
from dashboards.shared.constants import KEY_UID

class DashboardTransformConfigError(Exception):
    """Exception raised for errors in the division."""

    def __init__(self, message):
        self.message = message

class AbstractProcessor(ABC):

    """ TODO
    Redesign to:
     * Get rid off file and return {key:dashboard}: it's up to the children how to interpret key
     * The caller of this api is to take care of UID mapping in "url" links instead
     * Return a tuple of (dashboard, key), and the caller will know how to interpret key:
        - Global dashboard processor would interpret it as: (dashboard, <collector|global_key>)
        - Template dashboard processor would interpret it as: (dashboard, <template_key>)
        - Other processor (default): (dashboard, None)
    """
    @abstractmethod
    def process_dashboard(self, dashboard: Dict, key = None) -> Optional[List[Tuple[Dict, Optional[str]]]]:    # [(dashboard, <key>|None)]
        raise NotImplementedError
    

class DashboardProcessor(AbstractProcessor):

    def _traverse_update(self, element: Dict|List) -> None:
        """Traversing the passed in dashboard recursively and update as needed: root is dashboard root.
        """
        if isinstance(element, Dict):
            for item in element.items():          
                key, value = item
                if isinstance(value, Dict|List):         # key:value(Dict|List)
                    self._traverse_update(value)
                # TODO: process item as key:value. possibly:
                # dict_item__edit_item_by_match(...)
                # dict_dict_item__delete_item_by_key(element, owner_key, child_key)
                # dict_dict_item__delete_item_by_key_value(element, owner_key, (key, value))
                # dict_item__replace_value(...)
        elif isinstance(element, list):             # dict_list
            # TODO: process List item
            # 1...add/remove
            # 2...
            for item in element:                    # dict_list_<item>
                if isinstance(item, Dict)or isinstance(item, List):
                    # print(f'{element} - {item}')
                    self._traverse_update(item)
                else:                               # dict_list_<str|bool|int|float>
                    # TODO: process
                    pass


    def process_dashboard(self, dashboard: Dict, key = None) -> Optional[List[Tuple[Dict, Optional[str]]]]:    # [(dashboard, <key>|None)]
        if not dashboard: 
            raise DashboardTransformError('The dashboard to convert is empty. Please check the passed in dashboard.')
        # convert
        converted_dashboards: List[Tuple[Dict, Optional[str]]] = list()
        self._traverse_update(dashboard)
        converted_dashboards.append((dashboard, dashboard[KEY_UID]))
        return converted_dashboards

if __name__ == "__main__":
    file =  "/Users/mzheng/Work/community-dashboards/dashboards/test/Application_Overview.json"
    with open(file, 'r') as f:
        dash = json.load(f)
    processor = DashboardProcessor()
    processor.process_dashboard(dash)