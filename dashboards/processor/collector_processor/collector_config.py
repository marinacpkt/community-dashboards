
import json
import os
import random
import re
from typing import Dict, List, Optional, Set, Tuple
from dashboards.processor.dashboard_processor import DashboardTransformConfigError
from dashboards.editor.dashboard_editor import DashboardTransformError
# as suffix
RENAME_GLOBAL_DASHBOARDS = {'uid': 'global', 'title': 'Global'}  
# TODO
COLLECTOR_DS_MAPPINGS_FROM_GRAFANA = False
CREATE_DS_FOR_COLLECTORS = False
# uid
MAX_UID_LENGTH = 40
MAX_SUFFIX_LENGTH = 5
    

class CollectorConfigs:

    def __init__(self, config_file: str, glogal_uid_list: List[str], collector_uid_list: List[str]):
        if not glogal_uid_list and not collector_uid_list:
            raise DashboardTransformConfigError('UID mappings are required to conver dashboards for collectors.')
        # list of internal states
        self._config_dict: Dict = dict()
        self._collector_mappings: Dict[str,Tuple[Dict[str, str], Dict[str, str]]] = dict()  # {collector_key:({cclear_text:collector_text}, {cclear_ds:collector_ds})
        self._glogal_uids: Dict[str, str] = dict()                                 # {old_uid:new_uid}
        self._collector_uids: Dict[str, Dict[str, str]] = dict()                   # {collector:{old_uid:new_uid}}
        # update
        self._load_configs(config_file)
        # update uid mappings
        self._update_uid_mappings(glogal_uid_list, collector_uid_list)

    # for internal access only
    def _update_uid_mappings(self, glogal_uid_list: List[str], collector_uid_list: List[str]):
        """ Allow a maximum of 5 chars to collector. Generated uid cannot duplicate any other converted from the input folder. 
        NOTE: should compare against pre converted as well, ideally...
        """
        uid_set: Set = set()
        if glogal_uid_list:
            for uid in glogal_uid_list:
                uid_mapped = self._get_mapped_uid(uid, RENAME_GLOBAL_DASHBOARDS['uid'], uid_set)
                self._glogal_uids[uid] = uid_mapped
                uid_set.add(uid_mapped)
                # print(f'global mapping: {uid} - {uid_mapped}')
        if collector_uid_list:
            for uid in collector_uid_list:
                for collector in self._collector_mappings.keys():
                    uid_mapped = self._get_mapped_uid(uid, collector, uid_set)
                    if collector in self._collector_uids.keys():
                        self._collector_uids[collector].update({uid:uid_mapped})
                    else:
                        self._collector_uids[collector] = {uid:uid_mapped}
                    uid_set.add(uid_mapped)
                    # print(f'collector {collector}: {uid} - {uid_mapped}')   
    # for internal access only
    def _get_mapped_uid(self, uid, suffix, uid_set: Set) -> str:
        suffix_length = max(len(suffix), MAX_SUFFIX_LENGTH)
        max_uid_length = MAX_UID_LENGTH - suffix_length
        modified_uid = uid if len(uid) <= max_uid_length else uid[:max_uid_length]
        uid_mapped = f'{modified_uid}_{suffix}'
        uid_original_with_max = uid if len(uid) <= MAX_UID_LENGTH else uid[:MAX_UID_LENGTH]
        while uid_mapped == uid_original_with_max or uid_mapped in uid_set:
            uid_mapped_list = list(uid_mapped)
            random.shuffle(uid_mapped_list)
            uid_mapped = ''.join(uid_mapped_list)
        return uid_mapped

    # for internal access only
    def _load_configs(self, file: str):
        if not file or not os.path.exists(file):
            raise DashboardTransformConfigError(f'File/folder not specified or does not exist: {file}')
        if os.path.isfile(file) and not (os.path.basename(file).endswith('.json') or os.path.basename(file).endswith('.jsonc')):
            raise DashboardTransformConfigError(f'File specified is not a dashboard .json file: {file}')
        with open(file, 'r') as f:
            content = f.read()
            content = re.sub(r'//.*?\n|/\*.*?\*/', '', content, flags=re.S)
            self._config_dict = json.loads(content)
        # Gather different data structure and cache for future requests:
        # 1. text and datasource schema from cclear
        cclear: Dict = self._config_dict["cclear"]
        cclear_text: Dict = cclear["text"]
        cclear_datasources: Dict = cclear["datasources"]
        # 2. text and datasource mappings from collectors per collector
        for collector in self._config_dict["collectors"]:
            collector_key = collector["key"]
            collector_text = collector["text"]
            collector_datasources = collector["datasources"]
            lbl_maps: Dict[str, str] = dict()
            ds_maps: Dict[str, str] = dict()
            for text_key in cclear_text:
                lbl_maps[cclear_text[text_key]] = collector_text[text_key]
            for ds_key in cclear_datasources:
                ds_maps[cclear_datasources[ds_key]] = collector_datasources[ds_key]
            self._collector_mappings[collector_key] = (lbl_maps, ds_maps)

    def get_cclear_config(self):
        return self._config_dict["cclear"]
    
    def get_cclear_name(self) -> str:
        return self._config_dict['cclear']['text']['name']

    def get_collector_keys(self):
        return self._collector_mappings.keys()
            
    def get_text_mappings(self, collector_key: str) -> Dict[str, str]:
        return self._collector_mappings[collector_key][0]
    
    def get_datasource_mappings(self, collector_key: str) -> Dict[str, str]:
        return self._collector_mappings[collector_key][1]

    def get_mapping_for_ds(self, ds_original: str) -> Optional[List[Tuple[str, str]]]:  # List[collector_key:collector_ds]
        from dashboards.shared.constants import DS_IGNORED
        if not ds_original or len(ds_original) == 0:
            return None
        if any(ds in ds_original.lower() for ds in DS_IGNORED):
            return None
        ds_mapping: List[Tuple[str, str]] = list()
        cclear = self._config_dict["cclear"]
        ds_key = ds_original
        # find key to the ds value
        for key, value in cclear.items():
            if value == ds_original:
                ds_key = key
        # with ds key, gather all mappings
        collectors = self._config_dict["collectors"]
        try:
            for collector in collectors:
                ds = collector["datasources"][ds_key]
                if not ds:
                    raise DashboardTransformError(f'Could not find mapping value for datasource {ds_original}. May need to create a mapping datasource for this.')
                ds_mapping.append((collector["key"], ds))
        except KeyError as ke:
            raise DashboardTransformError(f'Could not find mapping value for datasource {ds_original}. May need to create a mapping datasource for this. Nested KeyError: {ke}')
        return ds_mapping    

    def get_uid_mappings_for_collector(self, collector_key) -> Optional[Dict[str, str]]:    # {old_uid:new_uid}
        return self._collector_uids[collector_key] if self._collector_uids else None
    
    def get_uid_mappings_for_merged_collectors(self) -> Optional[Dict[str, str]]:    # {old_uid:new_uid}
        return self._glogal_uids if self._glogal_uids else None


if __name__ == "__main__":
    inst = CollectorConfigs("/Users/mzheng/Work/community-dashboards/dashboards/config/customer_config/hsbc_collectors.jsonc", [], [])

    print(f'get_collectors: {inst.get_collector_keys()}')
    keys = inst.get_collector_keys()
    for key in keys:
        print(f'get_text_mappings for collector {key}: {inst.get_text_mappings(key)}')
        print(f'get_ds_mappings for collector {key}: {inst.get_datasource_mappings(key)}')
    cclear_ds = inst.get_cclear_config()["datasources"]
    for ds in cclear_ds:
        print(f'get_mapping_for_ds for datasource {ds}: {inst.get_mapping_for_ds(ds)}')
