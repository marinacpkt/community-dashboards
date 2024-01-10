import json
import os
import re
import operator
from typing import Dict, List, Optional, Tuple

from dashboards.shared.commons import DashboardTransformError, AbstractDashboardEditor, get_ds_name, node_remove_from_dict_by_key, node_remove_from_list_by_match, node_remove_from_nested_dict_by_keys, leaf_node_replace,query_add_tag_to_groupby, create_new_influxdb_datasource, overrides_update_links
from dashboards.shared.constants import OPTIONS_DEFAULT_ALL, DATASOURCE_MIXED, ON_DEMAND_MEASUREMENTS, QUERY_REFID_SEQUENCE, DS_INDICATORS
from dashboards.convert.collectorconverter.collector_config import FOLDERS_WITH_MERGED_GLOBAL_DASHBOARDS, get_mapping_for_ds, COLLECTOR_MAPPINGS, get_local_collector_label

# NOTE: restrictions to merged global cclear converter: only handle one panel per row kind of dashboards.
# Otherwise the y positions are likely messed up as new panels get added to the dashboard without handling positions

def remove_nm_from_query(query_element: Dict) -> Dict:
    key = 'query'
    if isinstance(query_element, Dict) and key in query_element.keys():
        leaf_node_replace(query_element, key, '(?i)AND\s+\"network_monitor_name\"\s*=~\s*/\^\$network_monitor\$/',"")
        leaf_node_replace(query_element, key, '"network_monitor_name"\s+=~\s+/\^\$network_monitor\$/\s+(?i)AND', "",)
        leaf_node_replace(query_element, key, '(?i)AND\s+\"network_monitor_name\"\s*=~\s*/\^\$\{network_monitor\}\$/', "" )
        leaf_node_replace(query_element, key, '"network_monitor_name"\s+=~\s+/\^\$\{network_monitor\}\$/\s+(?i)AND', "")
        leaf_node_replace(query_element, key, ' "network_monitor_name",', "")
        leaf_node_replace(query_element, key, ',\s*"network_monitor_name"', "")
        leaf_node_replace(query_element, key, '\(\\"network_monitor_name\\"\s*=~\s*/\^\$network_monitor\$/\)\s+(?i)AND', "")
        leaf_node_replace(query_element, key, '\,\s*network_monitor_name\s*', " ")
        leaf_node_replace(query_element, key, 'with\s+key =\s+\\"network_monitor_name\\"', " ")
        leaf_node_replace(query_element, key, '\"network_monitor_name\"', " ")
    return query_element

def remove_nm_from_link(url_element: Dict) -> Dict:
    key = 'url'
    if  isinstance(url_element, Dict) and key in url_element.keys():
        leaf_node_replace(url_element, key, '&var-network_monitor=\﻿\$\{network_monitor\}', "")
        leaf_node_replace(url_element, key, '&var-network_monitor=﻿\$\{network_monitor\}', "")
        leaf_node_replace(url_element, key, '&var-network_monitor=\$\{network_monitor\}', "")
        leaf_node_replace(url_element, key, '&var-network_monitor=\ufeff*\$\{network_monitor\}\ufeff*', "")
        leaf_node_replace(url_element, key, '&var-network_monitor=\ufeff*\$\{network_monitor\:text\}\ufeff*', "")
        leaf_node_replace(url_element, key, '&var-network_monitor=\$\{network_monitor\:text\}', "")
        leaf_node_replace(url_element, key, '\?var-network_monitor=\$\{network_monitor\}\&', "?")
        leaf_node_replace(url_element, key, '\&var-network_monitor=\$network_monitor', "")
        leaf_node_replace(url_element, key, '\&?var-network_monitor=.*', "")
    return url_element

def remove_nm_from_title(title_element: Dict) -> Dict:
    key = 'title'
    if  isinstance(title_element, Dict) and key in title_element.keys():
        leaf_node_replace(title_element, key, "\s+and\s+network\s+monitor\)", ")")
        leaf_node_replace(title_element, key, "\s+and\s+network\s+monitor\)", ")")
        leaf_node_replace(title_element, key, ",\s+network\s+monitor\s+and", " and")
        leaf_node_replace(title_element, key, "\$network_monitor:", "")
        leaf_node_replace(title_element, key, "\$network_monitor", "")
        leaf_node_replace(title_element, key, "\$\{network_monitor\}", "")
        leaf_node_replace(title_element, key, "\$\{network_monitor\:text\}", "")
        leaf_node_replace(title_element, key, "\s*\-\s*\$network_monitor", "")
        leaf_node_replace(title_element, key, ",\s*network monitor", "")
        leaf_node_replace(title_element, key, "\s*by\s+Network\s+Monitor", "")
    return title_element

def remove_nm_from_alias(alias_element: Dict) -> Dict:
    key = 'alias'
    if  isinstance(alias_element, Dict) and key in alias_element.keys():
        leaf_node_replace(alias_element, key, "\,\s*\$tag_network_monitor_name", "")
        leaf_node_replace(alias_element, key, "\:\s*\$tag_network_monitor_name", "")
        leaf_node_replace(alias_element, key, "\(alias_element, key, \$tag_network_monitor_name\)", "")
        leaf_node_replace(alias_element, key, "\s*-\s*\$tag_network_monitor_name", "")
        leaf_node_replace(alias_element, key, "\$tag_network_monitor_name\s*-\s*", "")
        leaf_node_replace(alias_element, key, "\$tag_network_monitor_name\s*", "")
    return alias_element

def remove_nm_str_replace(dash_element):
    remove_nm_from_link(dash_element)
    remove_nm_from_title(dash_element)
    remove_nm_from_query(dash_element)
    remove_nm_from_alias(dash_element)
    leaf_node_replace(dash_element, 'repeat', 'network_monitor', '')

# tree node: breadth first
# leaf node: deapth first
def remove_nm_from_dash(dash_element: Dict | List):
    if isinstance(dash_element, List):
        for item in dash_element:
            remove_nm_from_dash(item)
            remove_nm_str_replace(item)
    elif isinstance(dash_element, Dict):
        # remove matching dict element from dict: child of dash_element to remove
        node_remove_from_dict_by_key(dash_element, 'excludeByName')
        for item in dash_element.copy().items():
            key, value = item
            # depth first
            if isinstance(value, Dict):
                node_remove_from_nested_dict_by_keys(dash_element, 'fields', 'network_monitor_name')
                node_remove_from_nested_dict_by_keys(dash_element, 'fields', 'Network Monitor')
                node_remove_from_nested_dict_by_keys(dash_element, 'indexByName', 'network_monitor_name')
                node_remove_from_nested_dict_by_keys(dash_element, 'renameByName', 'network_monitor_name')
                remove_nm_from_dash(dash_element[key] )
            elif isinstance(value, List):
                # remove matching list element from list of dict[key]: matching grandchild(LOL) to remove, and child remove if no grandchild left...O_O
                node_remove_from_list_by_match(dash_element, 'tags', [('key', operator.eq, 'network_monitor_name')])
                node_remove_from_list_by_match(dash_element, 'list', [('name', operator.eq, 'network_monitor')])
                # TODO: handle 'network_monitor_name::tag'
                node_remove_from_list_by_match(dash_element, 'groupBy', [('params', operator.contains, 'network_monitor_name'), ('params',operator.contains, 'network_monitor')])
                node_remove_from_list_by_match(dash_element, 'select', [('params', operator.contains, 'network_monitor_name'), ('params',operator.contains, 'network_monitor')])
                node_remove_from_list_by_match(dash_element, 'fields', [(None, operator.contains, '(?i)network\s+(?i)monitor')])
                remove_nm_from_dash(dash_element[key])
            else:  # leaf node
                remove_nm_str_replace(dash_element)
    else:
        # raise DashboardTransformError('traverse_update takes only Dict or List element (allowed by dashboard elements). Please validate the dashboard on schema.')   
        pass

def update_graph_panel(panel: Dict):
    ds_name = get_ds_name(panel["datasource"])
    # start duplicating per collector ds of the same db
    ds_mapped: Optional[List[Tuple[str, str]]] = get_mapping_for_ds(ds_name)
    if ds_mapped:
        # ds to be mixed
        panel["datasource"] = DATASOURCE_MIXED
        # targets (list)
        targets: List = panel["targets"]
        refIds = [target['refId'] for target in targets]
        refId_latest = max(refIds)
        index = QUERY_REFID_SEQUENCE.index(refId_latest)
        duplicated_targets = []
        is_on_demand = False
        for target in targets:
            # add cstor_name to groupby
            query_add_tag_to_groupby(target, 'cstor_name', ',\s*\"?cstor_name\"?|\"?cstor_name\"?\s*,/g', get_local_collector_label())     
            # duplicate queries one per datasource, update datasource uid
            if not is_on_demand:
                for new_collector_key, new_collector_ds in ds_mapped:
                    new_target = target.copy()
                    # update query datasource
                    new_target["datasource"] = create_new_influxdb_datasource(new_collector_ds)
                    # update query refId
                    index = index + 1
                    new_target["refId"] = QUERY_REFID_SEQUENCE[index]
                    # update alias with new collector label: replace the original with new
                    new_label: Dict[str, str] = COLLECTOR_MAPPINGS[new_collector_key][0]
                    alias = new_target["alias"]
                    for key, value in new_label.items():
                        alias = alias.replace(key, value)
                    new_target["alias"] = alias
                    duplicated_targets.append(new_target)
        # add duplicated targets
        for nt in duplicated_targets:
            targets.append(nt)

def variable_single_multi_all(variable_element: Dict, variable_name: str, data_source: Dict, multi: bool, all: bool, query: str) -> Dict:
    if not isinstance(variable_element, Dict) or "name" not in variable_element.keys() or variable_element["name"] != variable_name:
        return variable_element
    variable_element["current"] = OPTIONS_DEFAULT_ALL
    variable_element["includeAll"] = all
    variable_element["multi"] = multi
    variable_element["datasource"] = data_source
    variable_element["query"] = query
    return variable_element

def convert_variables(variables: List) -> List:
    if isinstance(variables, List):
        for index, variable in enumerate(variables):
            variable_single_multi_all(variable, "cstor_name", DS_INDICATORS, True, True, 'show tag values from cstor_ports with key="cstor_name"')
            variable_single_multi_all(variable, "cstor_ip", DS_INDICATORS, True, True, 'show tag values from cstor_ports with key="cstor_ip" where cstor_name =~ /^$cstor_name$/')
    return variables

def update_panel_position_y(position_element: Dict, current_posion_y: int) -> Tuple[Dict, int]:
    gridPos = position_element.copy()
    gridPos["y"] = current_posion_y
    next_position_y = current_posion_y + gridPos["h"]
    return gridPos, next_position_y

def is_target_querying_from_on_demand(targets_element: Dict) -> bool:
    for target in targets_element:
        if "query" in target:
            query = target["query"]
            if any(ondemand in query for ondemand in ON_DEMAND_MEASUREMENTS):
                return True
    return False

# TODO: validate index correctness and if necessary
def convert_panels(owner, panels, y_axis):
    new_panels = []
    index = 0
    for panel in panels:
        # row
        if panel["type"] == "row":
            # breadth first to maintain parent position and orders
            panel["gridPos"], y_axis  = update_panel_position_y(panel['gridPos'], y_axis)
            new_panels.insert(index, panel)
            index = index + 1
            # children
            if "panels" in panel and panel["panels"]:
                convert_panels(panel, panel["panels"], y_axis)
        # graph (timeseries)
        elif panel["type"] == "timeseries":
            update_graph_panel(panel)
            panel["gridPos"], y_axis  = update_panel_position_y(panel['gridPos'], y_axis)
            new_panels.insert(index, panel)
            index = index + 1
        # on-demand collector
        elif panel["type"] == "cclear-ondemand-panel":
            ds = "tcp_4_Tuple" if "TCP" in owner["title"] else "flow_data_4_Tuple"
            ds = ds.replace("4", "5") if "5 Tuple" in owner["title"] else ds
            # TODO: other analytics
            options = panel["options"]
            options["ltType"] = "Analytics, cStor and IP/CIDR "
            options["analyticsType"] = ds
            options["nmName"] = ""
            options["cStorName"] = "${cstor_name:raw}"
            new_panels.insert(index, panel)
            index = index + 1
        # table: TODO: validate panel position esp. the original local panel?
        elif panel["type"] == "table":
            ds_name = get_ds_name(panel["datasource"])
            ds_mapped: Optional[List[Tuple[str, str]]] = get_mapping_for_ds(ds_name)
            if ds_mapped:
                # y axis
                panel["gridPos"], y_axis  = update_panel_position_y(panel['gridPos'], y_axis)
                # transform: assuming only one "organize" transform per table
                if 'transformations' in panel.keys():
                    organize = [x for x in panel["transformations"] if x["id"] == "organize"]
                    if organize and 'options' in organize[0].keys():
                        options = organize[0]["options"]
                        options["renameByName"] = {"cstor_name": "cStor Name"}
                        options["indexByName"] = {"cstor_name": 0}
                        options["excludeByName"] = {"Time": True}
                # check if contains on demand measurements
                is_on_demand = is_target_querying_from_on_demand(panel["targets"])
                if not is_on_demand:
                    # title
                    panel["title"] = f'"({get_local_collector_label()}) "{panel["title"]}'
                    overrides = panel["fieldConfig"]["overrides"]
                    panel["fieldConfig"]["overrides"] = links_csotr_to_all(overrides)
                new_panels.insert(index, panel)
                index = index + 1
                if not is_on_demand:
                    for new_collector_key, new_collector_ds in ds_mapped:
                        new_panel = panel.copy()
                        # title
                        new_label: Dict[str, str] = COLLECTOR_MAPPINGS[new_collector_key][0]
                        if new_label:
                            title = new_panel["title"]
                            for key, value in new_label.items():
                                title = title.replace(key, value)
                            new_panel["title"] = title
                        # y axis
                        new_panel["gridPos"], y_axis  = update_panel_position_y(new_panel['gridPos'], y_axis)
                        # datasource
                        new_panel["datasource"] = create_new_influxdb_datasource(new_collector_ds)
                        targets = new_panel["targets"]
                        for target in targets:
                            target["datasource"] = create_new_influxdb_datasource(new_collector_ds)
                        # panel position in order
                        new_panels.insert(index, new_panel)
                        index = index + 1
        else:
            panel["gridPos"], y_axis  = update_panel_position_y(panel['gridPos'], y_axis)
            new_panels.insert(index, panel)
            index = index + 1
    owner["panels"] = new_panels

def links_csotr_to_all(override_element: List) -> List:
    mappings: List[Tuple[str, str]] = list()
    mappings.append(("var\-cstor_name=\$\{cstor_name\:text\}","var-cstor_name=.*"))
    mappings.append(("var\-cstor_name=\$\{cstor_name\}","var-cstor_name=.*"))
    mappings.append(("var\-cstor_name=\$cstor_name","var-cstor_name=.*"))
    mappings.append(("var\-cstor_ip=\$\{cstor_ip\:text\}","var-cstor_ip=.*"))
    mappings.append(("var\-cstor_ip=\$\{cstor_ip\}","var-cstor_ip=.*"))
    mappings.append(("var\-cstor_ip=\$cstor_ip","var-cstor_ip=.*"))
    overrides_update_links(override_element, mappings)
    return override_element

class GlobalMergedCollectorConverter(AbstractDashboardEditor):

    @staticmethod
    def from_file(file: str, key: Optional[str] = None) -> Optional[List[Tuple[Dict, Optional[str]]]]:
        if file is None or len(file.strip()) == 0: 
            raise DashboardTransformError('The file path is an empty str. Please check the passed in file.')
        if not file.strip().endswith('.json'):
            raise DashboardTransformError(f'The file is not a .json dashboard file: {file}')
        if not os.path.exists(file.strip()): 
            raise DashboardTransformError(f'The file passed in does not exist: {file}')
        # convert according to only specified folders FOLDERS_WITH_SEPARATE_GLOBAL_DASHBOARDS
        input_path = os.path.dirname(file)
        parent_dir_name = os.path.basename(input_path)
        if parent_dir_name not in FOLDERS_WITH_MERGED_GLOBAL_DASHBOARDS: 
            return None
        # convert
        converted_dashboards: List[Tuple[Dict, Optional[str]]] = list()
        with open(file, "r") as dash_json:
            dash_obj: Dict = json.load(dash_json)
            converted_dashboards.append((GlobalMergedCollectorConverter.from_object(dash_obj), os.path.basename(file)))
            return converted_dashboards
    
    @staticmethod
    def from_object(dash_obj: Dict) -> Dict:
        if not dash_obj: 
            raise DashboardTransformError('The dashboard to convert is empty. Please check the passed in dashboard.')
        remove_nm_from_dash(dash_obj)
        if 'templating' in dash_obj.keys() and 'list' in dash_obj["templating"]:
            variables = dash_obj["templating"]["list"]
            convert_variables(variables)
        if 'panels' in dash_obj.keys() and dash_obj["panels"]:
            convert_panels(dash_obj, dash_obj["panels"], 0)
        return dash_obj

if __name__ == '__main__':
  pass
