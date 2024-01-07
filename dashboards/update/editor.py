import json
import os
from typing import Callable, Dict, List, Optional, Tuple
from dashboards.shared.commons import AbstractDashboardEditor, DashboardTransformError


def transform1(dash_element: Dict) -> Dict:
    # TODO
    print('transform1 called by Callable')
    return {}

def transform2(dash_element: Dict) -> Dict:
    # TODO
    print('transform2 called by Callable')
    return {}

class Editor(AbstractDashboardEditor):

    @staticmethod
    def traverse_update_global_separate(dash_element: Dict, datasource_mapping: Dict) -> None:
        """Traversing the passed in dashboard recursively and update as needed: root is dashboard root.
        """
        if isinstance(dash_element, Dict):
            # TODO: process Dict
            for value in dash_element.values():
                Editor.traverse_update_global_separate(value, datasource_mapping)
        elif isinstance(dash_element, list):
            for item in dash_element:
                Editor.traverse_update_global_separate(item, datasource_mapping)

    @staticmethod
    def from_object(dash_obj: Dict, transforms: List[Callable[[Dict], Dict]]) -> Tuple[Dict, bool]:
        if not dash_obj: 
            raise DashboardTransformError('The dashboard to convert is empty. Please check the passed in dashboard.')
        # TODO: Callable...
        for transform in transforms:
            transform({})
        return dash_obj, True
    
    @staticmethod
    def from_file(file: str) -> Optional[List[Tuple[Dict, Optional[str]]]]:
        if file is None or len(file.strip()) == 0: 
            raise DashboardTransformError('The file path is an empty str. Please check the passed in file.')
        if not file.strip().endswith('.json'):
            raise DashboardTransformError(f'The file is not a .json dashboard file: {file}')
        if not os.path.exists(file.strip()): 
            raise DashboardTransformError(f'The file passed in does not exist: {file}')
        # convert
        converted_dashboards: List[Tuple[Dict, Optional[str]]] = list()
        trans: List[Callable[[Dict], Dict]] = list()
        trans.append(transform1)
        trans.append(transform2)
        with open(file, "r") as dash_json:
            dash_obj = json.load(dash_json)
            # TODO
            transform_result, is_modified = Editor.from_object(dash_obj, trans)
            if is_modified:
                converted_dashboards.append((transform_result, file))
            return converted_dashboards


if __name__ == '__main__':
    Editor.from_file('/Users/mzheng/Workspace/grafana_publish/grafana-cclear-utility-bundle/src/assets/dashboards/ip_troubleshooting/ip_troubleshooting.json')

    