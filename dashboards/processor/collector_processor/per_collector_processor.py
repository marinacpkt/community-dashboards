import copy
import re
from typing import Dict, List, Optional, Tuple
from dashboards.processor.collector_processor.collector_config import CollectorConfigs
from dashboards.processor.dashboard_processor import  DashboardTransformError, AbstractProcessor
from dashboards.editor.dashboard_editor import get_ds_name
from dashboards.shared.constants import DS_IGNORED, KEY_DATASOURCE, KEY_TITLE, KEY_UID

def replace_datasource(dash_element: Dict, datasource_mapping: Dict) -> None:
    """ Replace the 'datasource' property of the datasource_object with the mapping datasource from the datasource_mapping
    """
    if isinstance(dash_element, Dict) and KEY_DATASOURCE in dash_element.keys(): 
        ds_original = get_ds_name(dash_element[KEY_DATASOURCE]).strip()
        if len(ds_original) > 0 and not any(ds in ds_original.lower() for ds in DS_IGNORED):
            try:
                ds_collector = datasource_mapping[ds_original]
                dash_element[KEY_DATASOURCE] = ds_collector
            except KeyError as ke:
                raise DashboardTransformError(f'Could not find mapping value for datasource {ds_original}. May need to create a mapping datasource for this. Nested KeyError: {ke}')

class PerCollectorProcessor(AbstractProcessor):

    def __init__(self, config: CollectorConfigs) -> None:
        super().__init__()
        self._config = config

    def traverse_update(self, dash_element: Dict | Dict, datasource_mapping: Dict, uid_mappings: Dict[str, str]) -> None:
        """Traversing the passed in dashboard recursively and update as needed: root is dashboard root.
        """
        if isinstance(dash_element, Dict):
            for value in dash_element.values():
                self.traverse_update(value, datasource_mapping, uid_mappings)
            # update data source to new datasources
            if KEY_DATASOURCE in dash_element.keys():
                replace_datasource(dash_element, datasource_mapping)
            # update links with new uids
            if uid_mappings and "url" in dash_element.keys():
                url = dash_element['url']
                if url:
                    for uid, uid_mapped in uid_mappings.items():
                        re.sub(uid, uid_mapped, url)
        elif isinstance(dash_element, List):
            for item in dash_element:
                self.traverse_update(item, datasource_mapping, uid_mappings)

    # override
    def process_dashboard(self, dashboard: Dict, key = None) -> Optional[List[Tuple[Dict, Optional[str]]]]:    # [(dashboard, <key>|None)]
        if not dashboard: 
            raise DashboardTransformError('The dashboard passed in is None. Please check the passed in dashboard')
        converted_dashboards: List[Tuple[Dict, Optional[str]]] = list()
        global_uid_mappings: Optional[Dict[str, str]] = self._config.get_uid_mappings_for_merged_collectors()
        for collector_key in self._config.get_collector_keys():
            collector_uid_mappings: Optional[Dict[str, str]] = self._config.get_uid_mappings_for_collector(collector_key)
            if not collector_uid_mappings or dashboard[KEY_UID] not in collector_uid_mappings.keys():
                return None
            text_mappings: Dict[str, str] = self._config.get_text_mappings(collector_key)
            datasource_mappings: Dict[str, str] = self._config.get_datasource_mappings(collector_key)
            dash_obj_copy: Dict = copy.deepcopy(dashboard)
            # title
            new_text = text_mappings[self._config.get_cclear_name()]
            dash_obj_copy[KEY_TITLE] = f"{dash_obj_copy[KEY_TITLE]} - {new_text}"
            # uid
            dash_obj_copy[KEY_UID] = collector_uid_mappings[dashboard[KEY_UID]]
            # uid mappings (ignoring the following line because Mypy is wrong that uid_mappings can be None!)
            uid_mappings: Dict[str, str] = collector_uid_mappings if not global_uid_mappings else {**global_uid_mappings, **collector_uid_mappings}  # type: ignore 
            # convert
            self.traverse_update(dash_obj_copy, datasource_mappings, uid_mappings)
            # return
            converted_dashboards.append((dash_obj_copy, f'{collector_key}_{new_text}'))
        return converted_dashboards
