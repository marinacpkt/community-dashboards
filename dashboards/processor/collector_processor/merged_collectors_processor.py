import operator
import re
from typing import Any, Dict, List, Optional, Tuple
from dashboards.processor.collector_processor.collector_config import CollectorConfigs
from dashboards.processor.dashboard_processor import AbstractProcessor
from dashboards.editor.dashboard_editor import DashboardTransformError, get_ds_name, query_add_tag_to_groupby, create_new_influxdb_datasource, overrides_update_links
from dashboards.shared.constants import OPTIONS_DEFAULT_ALL, DATASOURCE_MIXED, ON_DEMAND_MEASUREMENTS, QUERY_REFID_SEQUENCE, DS_INDICATORS, KEY_UID, KEY_TITLE, LOGICAL_OR, LOGICAL_AND
from dashboards.processor.collector_processor.collector_config import RENAME_GLOBAL_DASHBOARDS
from dashboards.editor.dashboard_editor import dict_item__edit_item_by_match, dict_item__replace_value_str, dict_item__replace_value_str_list, dict_list__delete_item_dict

# NOTE: restrictions to merged global cclear converter: only handle one panel per row kind of dashboards.
# Otherwise the y positions are likely messed up as new panels get added to the dashboard without handling positions
# TODO: consider prompt(warning) to users when width is not 24?
def remove_nm_from_query(query_element: Dict) -> Dict:
    matches: List[Tuple[str, str]] = list()
    matches.append(('(?i)AND\s+\"network_monitor_name\"\s*=~\s*/\^\$network_monitor\$/',""))
    matches.append(('"network_monitor_name"\s+=~\s+/\^\$network_monitor\$/\s+(?i)AND', "",))
    matches.append(('(?i)AND\s+\"network_monitor_name\"\s*=~\s*/\^\$\{network_monitor\}\$/', "" ))
    matches.append(('"network_monitor_name"\s+=~\s+/\^\$\{network_monitor\}\$/\s+(?i)AND', ""))
    matches.append((' "network_monitor_name",', ""))
    matches.append((',\s*"network_monitor_name"', ""))
    matches.append(('\(\\"network_monitor_name\\"\s*=~\s*/\^\$network_monitor\$/\)\s+(?i)AND', ""))
    matches.append(('\,\s*network_monitor_name\s*', " "))
    matches.append(('with\s+key =\s+\\"network_monitor_name\\"', " "))
    matches.append(('\"network_monitor_name\"', " "))
    dict_item__replace_value_str_list(query_element, 'query', matches)   # type: ignore
    return query_element

def remove_nm_from_link(url_element: Dict) -> Dict:
    matches: List[Tuple[str, str]] = list()
    matches.append(('&var-network_monitor=\﻿\$\{network_monitor\}', ""))
    matches.append(('&var-network_monitor=﻿\$\{network_monitor\}', ""))
    matches.append(('&var-network_monitor=\$\{network_monitor\}', ""))
    matches.append(('&var-network_monitor=\ufeff*\$\{network_monitor\}\ufeff*', ""))
    matches.append(('&var-network_monitor=\ufeff*\$\{network_monitor\:text\}\ufeff*', ""))
    matches.append(('&var-network_monitor=\$\{network_monitor\:text\}', ""))
    matches.append(('\?var-network_monitor=\$\{network_monitor\}\&', "?"))
    matches.append(('\&var-network_monitor=\$network_monitor', ""))
    matches.append(('\&?var-network_monitor=.*', ""))
    dict_item__replace_value_str_list(url_element, 'url', matches)   # type: ignore
    return url_element

def remove_nm_from_title(title_element: Dict) -> Dict:
    matches: List[Tuple[str, str]] = list()
    matches.append(("\s+and\s+network\s+monitor\)", ")"))
    matches.append(("\s+and\s+network\s+monitor\)", ")"))
    matches.append((",\s+network\s+monitor\s+and", " and"))
    matches.append(("\$network_monitor:", ""))
    matches.append(("\$network_monitor", ""))
    matches.append(("\$\{network_monitor\}", ""))
    matches.append(("\$\{network_monitor\:text\}", ""))
    matches.append(("\s*\-\s*\$network_monitor", ""))
    matches.append((",\s*network monitor", ""))
    matches.append(("\s*by\s+Network\s+Monitor", ""))
    dict_item__replace_value_str_list(title_element, 'title', matches)   # type: ignore
    return title_element

def remove_nm_from_alias(alias_element: Dict) -> Dict:
    matches: List[Tuple[str, str]] = list()
    matches.append(("\,\s*\$tag_network_monitor_name", ""))
    matches.append(("\:\s*\$tag_network_monitor_name", ""))
    matches.append(("\(alias_element, key, \$tag_network_monitor_name\)", ""))
    matches.append(("\s*-\s*\$tag_network_monitor_name", ""))
    matches.append(("\$tag_network_monitor_name\s*-\s*", ""))
    matches.append(("\$tag_network_monitor_name\s*", ""))
    dict_item__replace_value_str_list(alias_element, 'alias', matches)   # type: ignore
    return alias_element

# leaf node expected
def remove_nm_str_replace(dash_element):
    remove_nm_from_link(dash_element)
    remove_nm_from_title(dash_element)
    remove_nm_from_query(dash_element)
    # remove_nm_from_alias(dash_element)

def remove_nm_from_dash(dash_element: Dict | List):
    if isinstance(dash_element, List):
        for item in dash_element:
            remove_nm_from_dash(item)
    elif isinstance(dash_element, Dict):
        for item in dash_element.copy().items():
            key, value = item
            if isinstance(value, Dict):
                remove_nm_from_dash(dash_element[key] )
            elif isinstance(value, List):
                dict_list__delete_item_dict(dash_element, 'tags', [(LOGICAL_OR, 'key', operator.eq, 'network_monitor_name'), (LOGICAL_AND, 'value', operator.contains, '$network_monitor')])
                remove_nm_from_dash(dash_element[key])
            else:  # dash_element as key:value with value as str|bool|int|float
                remove_nm_str_replace(dash_element)
                dict_item__replace_value_str(dash_element, 'repeat', ('network_monitor', ""))

def variable_single_multi_all(variable_element: Dict, variable_name: str, data_source: Dict, multi: bool, all: bool, query: str) -> Dict:
    if not isinstance(variable_element, Dict) or "name" not in variable_element.keys() or variable_element["name"] != variable_name:
        return variable_element
    items: List[Tuple[str, Any]] = list()
    items.append(("query", query))
    items.append(("current", OPTIONS_DEFAULT_ALL))
    items.append(("includeAll", all))
    items.append(("multi", multi))
    items.append(("datasource", data_source))
    dict_item__edit_item_by_match(variable_element, ('name', variable_name), items)
    return variable_element

def convert_variables(variables: List) -> List:
    if isinstance(variables, List):
        for _, variable in enumerate(variables):
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

def search_replace(dash_element: Dict | List, element_key, uid_mappings: Dict[str,str]):
    if isinstance(dash_element, Dict):
        if element_key and element_key in dash_element.keys() and uid_mappings:
            for old_uid, new_uid in uid_mappings.items():
                dash_element[element_key] = re.sub(old_uid, new_uid, dash_element[element_key])
        for value in dash_element.values():
            if isinstance(value, Dict|List):
                search_replace(value, element_key, uid_mappings)
    elif isinstance(dash_element, List):
        for item in dash_element:
            search_replace(item, element_key, uid_mappings)
    else:
        if not element_key and uid_mappings:
            for old_uid, new_uid  in uid_mappings.items():
                dash_element[element_key] = re.sub(old_uid, new_uid, dash_element)
    return dash_element

class MergedCollectorsProcessor(AbstractProcessor):

    def __init__(self, config: CollectorConfigs):
        super().__init__()
        self._config = config
    
    # override
    def process_dashboard(self, dashboard: Dict, key = None) -> Optional[List[Tuple[Dict, Optional[str]]]]:    # [(dashboard, <key>|None)]
        if not dashboard: 
            raise DashboardTransformError('The dashboard to convert is empty. Please check the passed in dashboard.')
        global_uid_mappings: Optional[Dict[str, str]] = self._config.get_uid_mappings_for_merged_collectors()
        if not global_uid_mappings or dashboard[KEY_UID] not in global_uid_mappings.keys():
            return None
        # map global uids
        search_replace(dashboard, 'url', global_uid_mappings)
        # remove network monitor variable
        remove_nm_from_dash(dashboard)
        if 'templating' in dashboard.keys() and 'list' in dashboard["templating"]:
            templating: Dict = dashboard["templating"]
            dict_list__delete_item_dict(templating, 'list', [(LOGICAL_OR, 'name', operator.eq, 'network_monitor')])
            convert_variables(templating['list'])
        # update panels: esp duplicating table per collector
        if 'panels' in dashboard.keys() and dashboard["panels"]:
            self._convert_panels(dashboard, dashboard["panels"], 0)
        # uid
        dashboard[KEY_UID] = global_uid_mappings[dashboard[KEY_UID]]
        # title
        dashboard[KEY_TITLE] = RENAME_GLOBAL_DASHBOARDS[KEY_TITLE]
        # convert
        return [(dashboard, RENAME_GLOBAL_DASHBOARDS[KEY_UID])]

    def _convert_panels(self, owner, panels, y_axis):
        new_panels = []
        for panel in panels:
            # row
            if panel["type"] == "row":
                # breadth first to maintain parent position and orders
                panel["gridPos"], y_axis  = update_panel_position_y(panel['gridPos'], y_axis)
                new_panels.append(panel)
                # children
                if "panels" in panel and panel["panels"]:
                    self._convert_panels(panel, panel["panels"], y_axis)
            # graph (timeseries)
            elif panel["type"] == "timeseries":
                self._update_graph_panel(panel)
                panel["gridPos"], y_axis  = update_panel_position_y(panel['gridPos'], y_axis)
                new_panels.append(panel)
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
                new_panels.append(panel)
            # table: TODO: validate panel position esp. the original local panel?
            elif panel["type"] == "table":
                ds_name = get_ds_name(panel["datasource"])
                ds_mapped: Optional[List[Tuple[str, str]]] = self._config.get_mapping_for_ds(ds_name)
                if ds_mapped:
                    # y axis
                    panel["gridPos"], y_axis  = update_panel_position_y(panel['gridPos'], y_axis)
                    # add/update cstor name to transform: assuming only one "organize" transform per table
                    if 'transformations' in panel.keys():
                        organize = [x for x in panel["transformations"] if x["id"] == "organize"]
                        if organize and 'options' in organize[0].keys():
                            options = organize[0]["options"]
                            options["renameByName"] = {"cstor_name": "cStor Name"}
                            options["indexByName"] = {"cstor_name": 0}
                            options["excludeByName"] = {"Time": True}
                    # check if contains on demand measurements
                    is_on_demand = is_target_querying_from_on_demand(panel["targets"])
                    new_panels.append(panel)
                    if not is_on_demand:
                        # title
                        panel["title"] = f'({self._config.get_cclear_name()}) {panel["title"]}'
                        overrides = panel["fieldConfig"]["overrides"]
                        panel["fieldConfig"]["overrides"] = links_csotr_to_all(overrides)
                        for new_collector_key, new_collector_ds in ds_mapped:
                            new_panel = panel.copy()
                            # title
                            new_text: Dict[str, str] = self._config.get_text_mappings(new_collector_key)
                            if new_text:
                                title = new_panel["title"]
                                for key, value in new_text.items():
                                    title = title.replace(key, value)
                                new_panel["title"] = title
                            # y axis
                            new_panel["gridPos"], y_axis  = update_panel_position_y(new_panel['gridPos'], y_axis)
                            # datasource
                            new_panel["datasource"] = create_new_influxdb_datasource(new_collector_ds)
                            targets = new_panel["targets"]
                            for target in targets:
                                target["datasource"] = create_new_influxdb_datasource(new_collector_ds)
                            # map collector uids
                            collector_uid_mappings = self._config.get_uid_mappings_for_collector(new_collector_key)
                            if collector_uid_mappings:
                                search_replace(new_panel, 'url', collector_uid_mappings)
                            # panel position in order
                            new_panels.append(new_panel)
            else:
                panel["gridPos"], y_axis  = update_panel_position_y(panel['gridPos'], y_axis)
                new_panels.append(panel)
        owner["panels"] = new_panels
            
    def _update_graph_panel(self, panel: Dict):
        ds_name = get_ds_name(panel["datasource"])
        # start duplicating per collector ds of the same db
        ds_mapped: Optional[List[Tuple[str, str]]] = self._config.get_mapping_for_ds(ds_name)
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
                query_add_tag_to_groupby(target, 'cstor_name', ',\s*\"?cstor_name\"?|\"?cstor_name\"?\s*,/g', self._config.get_cclear_name())     
                # duplicate queries one per datasource, update datasource uid
                if not is_on_demand:
                    for new_collector_key, new_collector_ds in ds_mapped:
                        new_target = target.copy()
                        # update query datasource
                        new_target["datasource"] = create_new_influxdb_datasource(new_collector_ds)
                        # update query refId
                        index = index + 1
                        new_target["refId"] = QUERY_REFID_SEQUENCE[index]
                        # update alias with new collector text: replace the original with new
                        new_text: Dict[str, str] = self._config.get_text_mappings(new_collector_key)
                        alias = new_target["alias"]
                        for key, value in new_text.items():
                            alias = alias.replace(key, value)
                        new_target["alias"] = alias
                        duplicated_targets.append(new_target)
                        # map collector uids
                        collector_uid_mappings = self._config.get_uid_mappings_for_collector(new_collector_key)
                        if collector_uid_mappings:
                            search_replace(new_target, 'url', collector_uid_mappings)
            # add duplicated targets
            for nt in duplicated_targets:
                targets.append(nt)