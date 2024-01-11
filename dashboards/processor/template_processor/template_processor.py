import copy
from typing import Dict, List, Optional, Tuple
from dashboards.processor.dashboard_processor import AbstractProcessor
from dashboards.editor.dashboard_editor import DashboardTransformError, dict_dict_item__replace_key_list, dict_item__replace_value_str, dict_item__replace_value_str_list
from dashboards.config.application_constants import DASHBOARD_SETS_APPLICATIONS
from dashboards.shared.constants import KEY_TITLE


class TemplateProcessor(AbstractProcessor):

    def __init__(self, ) -> None:
        super().__init__()
        
    def traverse_update(self, element: Dict | List, label_mappings: List[Tuple[str, str]], schema_mapping: Tuple[str, str]) -> None:
        """Traversing the passed in dashboard recursively and update as needed: root is dashboard root.
        """
        if isinstance(element, Dict):
            # depth first
            for value in element.values():
                if isinstance(value, Dict|List):
                    self.traverse_update(value, label_mappings, schema_mapping)
                else:   # value as: str|bool|int|float owned by a dictionary
                    dict_item__replace_value_str_list(element, [KEY_TITLE,'query','byField', 'options', 'url', 'label', 'text', 'title'], label_mappings)
                    dict_item__replace_value_str_list(element, [KEY_TITLE,'url', 'options'], [schema_mapping])
                    dict_item__replace_value_str(element, 'query', schema_mapping)
                    # TODO: more transform
                    # ApplicationConverter.replace_key(dash_element, 'indexByName', schema_mapping)
                    dict_dict_item__replace_key_list(element, 'indexByName', label_mappings)
                    dict_item__replace_value_str(element, f'source_{schema_mapping[1]}', label_mappings[-1])
        elif isinstance(element, list):
            for item in element:
                if isinstance(item, Dict) is isinstance(element, List):
                    self.traverse_update(item, label_mappings, schema_mapping)
                else: # item as: str|bool|int|float owned by a list
                    dict_item__replace_value_str_list(item, [KEY_TITLE,'query','byField', 'options', 'url', 'label', 'text'], label_mappings)
                    dict_item__replace_value_str(item, 'query', schema_mapping)
                    # TODO: more transform
                    # ApplicationConverter.replace_key(dash_element, 'indexByName', schema_mapping)
                    dict_dict_item__replace_key_list(item, 'indexByName', label_mappings)
                    dict_item__replace_value_str(item, f'source_{schema_mapping[1]}', label_mappings[-1])
        else: # wrong schema. should never happend
            raise DashboardTransformError('traverse_update takes only Dict or List element (allowed by dashboard elements). Please validate the dashboard on schema.')
        
    def from_object_one_dashboard(self, dashboard: Dict, key_from: str, key_to) -> Dict:
        if not dashboard: 
            raise DashboardTransformError('The dashboard to convert is empty. Please check the passed in dashboard.')
        if key_from not in DASHBOARD_SETS_APPLICATIONS.keys() or key_to not in DASHBOARD_SETS_APPLICATIONS.keys():
            raise DashboardTransformError(f'The original application key is not set. Please specify which application is this dashboard about: {DASHBOARD_SETS_APPLICATIONS.keys()}')
        label_mappings: List[Tuple[str, str]] = list()
        for label_from in DASHBOARD_SETS_APPLICATIONS[key_from][1]:
            label_mappings.append((label_from, DASHBOARD_SETS_APPLICATIONS[key_to][1][-1]))
        schema_mapping = (DASHBOARD_SETS_APPLICATIONS[key_from][2], DASHBOARD_SETS_APPLICATIONS[key_to][2])
        self.traverse_update(dashboard, label_mappings, schema_mapping)
        return dashboard
    
    # override
    def process_dashboard(self, dashboard: Dict, key = None) -> Optional[List[Tuple[Dict, Optional[str]]]]:
        if not dashboard: 
            raise DashboardTransformError('The dashboard passed in is None. Please check the passed in dashboard')
        if not key or key not in DASHBOARD_SETS_APPLICATIONS.keys():
            raise DashboardTransformError(f'The original application key is not set. Please specify which application is this dashboard about: {DASHBOARD_SETS_APPLICATIONS.keys()}')
        # convert
        converted_dashboards: List[Tuple[Dict, Optional[str]]] = list()
        for key_to in DASHBOARD_SETS_APPLICATIONS.keys():
            if key_to != key:
                dash_obj_copy = copy.deepcopy(dashboard)
                converted = self.from_object_one_dashboard(dash_obj_copy, key, key_to)
                converted_dashboards.append((converted, f'{DASHBOARD_SETS_APPLICATIONS[key][0]}:{DASHBOARD_SETS_APPLICATIONS[key_to][0]}'))
        return converted_dashboards
    
if __name__ == '__main__':
    pass
