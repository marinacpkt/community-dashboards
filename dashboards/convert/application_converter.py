import json
import os
import copy
import re
from typing import Dict, List, Optional, Tuple
from dashboards.shared.commons import AbstractDashboardEditor, DashboardTransformError, replace_key_list, replace_value_str, replace_value_str_list
from dashboards.shared.constants import DASHBOARD_SETS_APPLICATIONS, KEY_TITLE


class ApplicationConverter(AbstractDashboardEditor):
        
    @staticmethod
    def traverse_update(dash_element: Dict | List, label_mappings: List[Tuple[str, str]], schema_mapping: Tuple[str, str]) -> None:
        """Traversing the passed in dashboard recursively and update as needed: root is dashboard root.
        """
        if isinstance(dash_element, Dict):
            # depth first
            for value in dash_element.values():
                if isinstance(value, Dict) or isinstance(value, List):
                    ApplicationConverter.traverse_update(value, label_mappings, schema_mapping)
            # leaf
            replace_value_str_list(dash_element, [KEY_TITLE,'query','byField', 'options', 'url', 'label', 'text'], label_mappings)
            replace_value_str(dash_element, 'query', schema_mapping)
            # ApplicationConverter.replace_key(dash_element, 'indexByName', schema_mapping)
            replace_key_list(dash_element, 'indexByName', label_mappings)
            replace_value_str(dash_element, f'source_{schema_mapping[1]}', label_mappings[-1])
        elif isinstance(dash_element, list):
            for item in dash_element:
                ApplicationConverter.traverse_update(item, label_mappings, schema_mapping)
        else: # wrong schema
            raise DashboardTransformError('traverse_update takes only Dict or List element (allowed by dashboard elements). Please validate the dashboard on schema.')
        
    @staticmethod
    def from_object(dash_obj: Dict, key_from: str, file: Optional[str] = None) -> Optional[List[Tuple[Dict, Optional[str]]]]:
        converted_dashboards: List[Tuple[Dict, Optional[str]]] = list()
        for key in DASHBOARD_SETS_APPLICATIONS.keys():
            if key != key_from:
                dash_obj_copy = copy.deepcopy(dash_obj)
                converted = ApplicationConverter.from_object_one_dashboard(dash_obj_copy, key_from, key)
                label_from = DASHBOARD_SETS_APPLICATIONS[key_from][0][-1]
                label_to = DASHBOARD_SETS_APPLICATIONS[key][0][-1]
                if file:
                    filename: str = os.path.basename(file)
                    if re.search(r'_', filename): 
                        label_to = re.sub('\s+', '_', label_to.lower())
                        label_from = re.sub('\s+', '_', label_from.lower())
                        filename_to = os.path.basename(file).lower().replace(label_from, label_to)
                    else:
                        filename_to = os.path.basename(file).replace(label_from, label_to)
                converted_dashboards.append((converted, filename_to))
        return converted_dashboards

    @staticmethod
    def from_object_one_dashboard(dash_obj: Dict, key_from: str, key_to) -> Dict:
        if not dash_obj: 
            raise DashboardTransformError('The dashboard to convert is empty. Please check the passed in dashboard.')
        if key_from not in DASHBOARD_SETS_APPLICATIONS.keys() or key_to not in DASHBOARD_SETS_APPLICATIONS.keys():
            raise DashboardTransformError(f'The original application key is not set. Please specify which application is this dashboard about: {DASHBOARD_SETS_APPLICATIONS.keys()}')
        label_mappings: List[Tuple[str, str]] = list()
        for label_from in DASHBOARD_SETS_APPLICATIONS[key_from][0]:
            label_mappings.append((label_from, DASHBOARD_SETS_APPLICATIONS[key_to][-1]))
        schema_mapping = (DASHBOARD_SETS_APPLICATIONS[key_from][1], DASHBOARD_SETS_APPLICATIONS[key_to][1])
        ApplicationConverter.traverse_update(dash_obj, label_mappings, schema_mapping)
        return dash_obj
    
    @staticmethod
    def from_file(file: str, application_from_key: Optional[str] = None) -> Optional[List[Tuple[Dict, Optional[str]]]]:
        if file is None or len(file.strip()) == 0: 
            raise DashboardTransformError('The file path is an empty str. Please check the passed in file.')
        if not file.strip().endswith('.json'):
            raise DashboardTransformError(f'The file is not a .json dashboard file: {file}')
        if not os.path.exists(file.strip()): 
            raise DashboardTransformError(f'The file passed in does not exist: {file}')
        if application_from_key not in DASHBOARD_SETS_APPLICATIONS.keys():
            raise DashboardTransformError(f'The original application key is not set. Please specify which application is this dashboard about: {DASHBOARD_SETS_APPLICATIONS.keys()}')
        # convert
        converted_dashboards: Optional[List[Tuple[Dict, Optional[str]]]] = list()
        with open(file, "r") as dash_json:
            dash_obj: Dict = json.load(dash_json)
            converted_dashboards = ApplicationConverter.from_object(dash_obj, application_from_key, file)
        return converted_dashboards
    
if __name__ == '__main__':
    pass
