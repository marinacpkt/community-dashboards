import json
import os
import copy
from typing import Dict, List, Optional, Tuple
from dashboards.shared.commons import AbstractDashboardEditor, DashboardTransformError, get_ds_name
from dashboards.shared.constants import DS_IGNORED, KEY_DATASOURCE, KEY_TITLE, KEY_UID
from dashboards.convert.collectorconverter.collector_config import COLLECTOR_MAPPINGS, FOLDERS_WITH_SEPARATE_GLOBAL_DASHBOARDS, COPY_FORWARD_ORIGINAL, OUTPUT_FOLDER_PER_COLLECTOR


def replace_datasource(datasource_object: Dict, datasource_mapping: Dict) -> None:
    """ Replace the 'datasource' property of the datasource_object with the mapping datasource from the datasource_mapping
    """
    if isinstance(datasource_object, Dict) and KEY_DATASOURCE in datasource_object.keys(): 
        ds_original = get_ds_name(datasource_object[KEY_DATASOURCE]).strip()
        if len(ds_original) > 0 and not any(ds in ds_original.lower() for ds in DS_IGNORED):
            try:
                ds_collector = datasource_mapping[ds_original]
                datasource_object[KEY_DATASOURCE] = ds_collector
            except KeyError as ke:
                raise DashboardTransformError(f'Could not find mapping value for datasource {ds_original}. May need to create a mapping datasource for this. Nested KeyError: {ke}')

class GlobalPerCollectorConverter(AbstractDashboardEditor):

    @staticmethod
    def from_file(file, key: Optional[str] = None) -> Optional[List[Tuple[Dict, Optional[str]]]]:
        """
        1. dashboard level:
        * add ' - DS_LABEL_MAPPING.<dc>' to the end of the dashboard 'title'
        * add '_<dc>' to the end of the dashboard uid
        2. Traverse each element: replace every "datasource" for each element
        3. Write to file: 
        * append collector key and label to file name. 
        * write to flat to folder or new folder per collector according to config OUTPUT_FOLDER_PER_COLLECTOR
        * copy forward the original file/dashboard according to config COPY_FORWARD_ORIGINAL
        """
        if not (file and len(file) > 0 and os.path.exists(file)):
            raise DashboardTransformError('The file path is an empty str. Please check the passed in file.')
        if not file.strip().endswith('.json'):
            raise DashboardTransformError(f'The file is not a .json dashboard file: {file}')
        if not os.path.exists(file.strip()): 
            raise DashboardTransformError(f'The file passed in does not exist: {file}')
        
        # convert according to only specified folders FOLDERS_WITH_SEPARATE_GLOBAL_DASHBOARDS
        input_path = os.path.dirname(file)
        parent_dir_name = os.path.basename(input_path)
        if parent_dir_name not in FOLDERS_WITH_SEPARATE_GLOBAL_DASHBOARDS:
            return None
        
        with open(file, "r") as dash_json:
            dash_obj = json.load(dash_json)
        # convert to dashboard per collector and write to file
        converted_dashboards = GlobalPerCollectorConverter.from_object(dash_obj, os.path.basename(file))
        return converted_dashboards

    @staticmethod
    def traverse_update_global_separate(dash_element: Dict, datasource_mapping: Dict) -> None:
        """Traversing the passed in dashboard recursively and update as needed: root is dashboard root.
        """
        if isinstance(dash_element, Dict):
            if KEY_DATASOURCE in dash_element.keys():
                replace_datasource(dash_element, datasource_mapping)
            for value in dash_element.values():
                GlobalPerCollectorConverter.traverse_update_global_separate(value, datasource_mapping)
        elif isinstance(dash_element, List):
            for item in dash_element:
                GlobalPerCollectorConverter.traverse_update_global_separate(item, datasource_mapping)

    @staticmethod
    def from_object( dash_obj: Dict, filename: Optional[str] = None) -> List[Tuple[Dict, Optional[str]]]:
        """TODO: convert to API"""
        if not dash_obj: 
            raise DashboardTransformError('The dashboard passed in is None. Please check the passed in dashboard')
        converted_dashboards: List[Tuple[Dict, Optional[str]]] = list()
        for collector_key, collector in COLLECTOR_MAPPINGS.items():
            label: str = collector[0]
            datasource_mapping: Dict = collector[1]
            dash_obj_copy: Dict = copy.deepcopy(dash_obj)
            dash_obj_copy[KEY_TITLE] = f"{dash_obj_copy[KEY_TITLE]} - {label}"
            dash_obj_copy[KEY_UID] = f"{dash_obj_copy[KEY_UID]}_{collector_key}"
            GlobalPerCollectorConverter.traverse_update_global_separate(dash_obj_copy, datasource_mapping)
            collector_output_file = None
            if filename and len(filename) > 0 :
                filename_copy = os.path.basename(filename).replace('.', f'_{collector_key}.')
                collector_output_file =  f'{collector_key}_{label}/{filename_copy}' if OUTPUT_FOLDER_PER_COLLECTOR else filename_copy
            converted_dashboards.append((dash_obj_copy, collector_output_file))
        # write original file as is
        if COPY_FORWARD_ORIGINAL:
            converted_dashboards.append((dash_obj, filename))
        return converted_dashboards
