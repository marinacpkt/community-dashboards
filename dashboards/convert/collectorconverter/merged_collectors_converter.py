import json
import os
import re
from typing import Dict, List, Optional, Tuple

from dashboards.shared.commons import DashboardTransformError, AbstractDashboardEditor, get_ds_name
from dashboards.shared.constants import CUSTOM_OPTIONS_DEFAULT_ALL, DATASOURCE_MIXED, ON_DEMAND_MEASUREMENTS, QUERY_REFID_SEQUENCE
from dashboards.convert.collectorconverter.collector_config import FOLDERS_WITH_MERGED_GLOBAL_DASHBOARDS, get_mapping_for_ds


def update_cstor_name(cstor_name):
    cstor_name["current"] = CUSTOM_OPTIONS_DEFAULT_ALL
    cstor_name["includeAll"] = "true"
    cstor_name["multi"] = "true"
    cstor_name["datasource"] = {
                                "type": "influxdb",
                                "uid": "indicators"
                                }
    cstor_name["query"] = 'show tag values from cstor_ports with key="cstor_name"'

def update_cstor_ip(cstor_ip):
    cstor_ip["current"] = CUSTOM_OPTIONS_DEFAULT_ALL
    cstor_ip["includeAll"] = "true"
    cstor_ip["multi"] = "true"
    cstor_ip["datasource"] = {
                                "type": "influxdb",
                                "uid": "indicators"
                                }
    cstor_ip["query"] = 'show tag values from cstor_ports with key="cstor_ip" where cstor_name =~ /^$cstor_name$/'


def remove_nm_dash(dash_obj):
    if isinstance(dash_obj, List):
        for ls in dash_obj:
            remove_nm_dash(ls)
    elif isinstance(dash_obj, Dict):
        for key, value in dash_obj.copy().items():
            if key == "url":
                dash_obj["url"] = remove_nm_link(value)
            elif key == "title":
                dash_obj["title"] = remove_nm_title(value)
            elif key == "excludeByName":
                del dash_obj["excludeByName"]
            elif key == "query":
                if isinstance(value, str):
                    dash_obj["query"] = remove_nm_query(value)
            elif key == "tags":
                tag_network_monitor = [nm for nm in value if isinstance(nm, Dict) and nm["key"]=="network_monitor_name"]
                if len(tag_network_monitor) > 0:
                    value.remove(tag_network_monitor[0])
            elif key == "alias":
                dash_obj["alias"]  = remove_nm_alias(value)
            elif key == "groupBy":
                groupby_network_monitor = [nm for nm in value if "network_monitor_name" in nm["params"] or "network_monitor" in nm["params"]]
                if len(groupby_network_monitor) > 0:
                    value.remove(groupby_network_monitor[0])
            elif key == "select":
                select_network_monitor = ""
                for select_inner in value:
                    select_network_monitor = [nm for nm in select_inner if "network_monitor_name" in nm["params"]]
                    if len(select_network_monitor) > 0:
                        select_inner.remove(select_network_monitor[0])
            elif key == "fields":
                fields_network_monitor = [nm for nm in value if "(?i)network\s+(?i)monitor" in nm]
                if len(fields_network_monitor) > 0:
                    value.remove("network_monitor_name")
                if isinstance(value, Dict) and "network_monitor_name" in value.keys():
                    del value["network_monitor_name"]
                if isinstance(value, Dict) and "Network Monitor" in value.keys():
                    del value["Network Monitor"]
            elif key == "indexByName":
                if "network_monitor_name" in value.keys():
                    del value["network_monitor_name"]
            elif key == "renameByName":
                if "network_monitor_name" in value.keys():
                    del value["network_monitor_name"]   
            else: 
                pass
    else:
        pass  # do nothing with other types: int, float, bool, None

def remove_nm_query(query):
    new_query = re.sub('(?i)AND\s+\"network_monitor_name\"\s*=~\s*/\^\$network_monitor\$/',"", query)
    new_query = re.sub('"network_monitor_name"\s+=~\s+/\^\$network_monitor\$/\s+(?i)AND', "", new_query)
    new_query = re.sub('(?i)AND\s+\"network_monitor_name\"\s*=~\s*/\^\$\{network_monitor\}\$/', "", new_query)
    new_query = re.sub('"network_monitor_name"\s+=~\s+/\^\$\{network_monitor\}\$/\s+(?i)AND', "", new_query)
    new_query = re.sub(' "network_monitor_name",', "", new_query)
    new_query = re.sub(',\s*"network_monitor_name"', "", new_query)
    new_query = re.sub('\(\\"network_monitor_name\\"\s*=~\s*/\^\$network_monitor\$/\)\s+(?i)AND', "", new_query)
    new_query = re.sub('\,\s*network_monitor_name\s*', " ", new_query)
    new_query = re.sub('with\s+key =\s+\\"network_monitor_name\\"', " ", new_query)
    return new_query

def remove_nm_link(url):
    new_url = re.sub('&var-network_monitor=\﻿\$\{network_monitor\}', "", url)
    new_url = re.sub('&var-network_monitor=﻿\$\{network_monitor\}', "", new_url)
    new_url = re.sub('&var-network_monitor=\$\{network_monitor\}', "", new_url)
    new_url = re.sub('&var-network_monitor=\ufeff*\$\{network_monitor\}\ufeff*', "", new_url)
    new_url = re.sub('&var-network_monitor=\ufeff*\$\{network_monitor\:text\}\ufeff*', "", new_url)
    new_url = re.sub('&var-network_monitor=\$\{network_monitor\:text\}', "", new_url)
    new_url = re.sub('\?var-network_monitor=\$\{network_monitor\}\&', "?", new_url)
    new_url = re.sub('\&var-network_monitor=\$network_monitor', "", new_url)
    return new_url

def remove_nm_title(title):
    new_title = re.sub("\s+and\s+network\s+monitor\)", ")", title)
    new_title = re.sub("\s+and\s+network\s+monitor\)", ")", new_title)
    new_title = re.sub(",\s+network\s+monitor\s+and", " and", new_title)
    new_title = re.sub("\$network_monitor:", "", new_title)
    new_title = re.sub("\$network_monitor", "", new_title)
    new_title = re.sub("\$\{network_monitor\}", "", new_title)
    new_title = re.sub("\$\{network_monitor\:text\}", "", new_title)
    new_title = re.sub("\s*\-\s*\$network_monitor", "", new_title)
    new_title = re.sub(",\s*network monitor", "", new_title)
    new_title = re.sub("\s*by\s+Network\s+Monitor", "", new_title)
    return new_title

def remove_nm_alias(alias):
    new_alias = re.sub("\,\s*\$tag_network_monitor_name", "", alias)
    new_alias = re.sub("\:\s*\$tag_network_monitor_name", "", new_alias)
    new_alias = re.sub("\(\$tag_network_monitor_name\)", "", new_alias)
    new_alias = re.sub("\s*-\s*\$tag_network_monitor_name", "", new_alias)
    new_alias = re.sub("\$tag_network_monitor_name\s*-\s*", "", new_alias)
    new_alias = re.sub("\$tag_network_monitor_name\s*", "", new_alias)
    return new_alias

def update_graph_panel(panel):
    ds_name = get_ds_name(panel["datasource"])
    # start duplicating per collector ds of the same db
    ds_mapped = get_mapping_for_ds(ds_name)
    if ds_mapped:
        # ds to be mixed
        panel["datasource"] = DATASOURCE_MIXED
        # targets (list)
        targets = panel["targets"]
        duplicated_targets = []
        index = 0
        is_on_demand = False
        for target in targets:
            # query
            if "query" in target and 'rawQuery' in target.keys() and target['rawQuery']:
                query = target["query"]
                # add cstor_name to groupby
                if not re.search(r',\s*\"?cstor_name\"?|\"?cstor_name\"?\s*,/g', query):
                    if "fill" in query:
                        fillIndex = query.rindex("fill")
                        query = query[:fillIndex] + ', "cstor_name" ' +query[fillIndex:]
                    else:
                        query = query + ', "cstor_name" '
                target["query"] = query
                if any(ondemand in query for ondemand in ON_DEMAND_MEASUREMENTS):
                    is_on_demand = True
            # groupby
            if "groupBy" in target.keys():
                groupby = target["groupBy"]
                groupby_cstor_name = [cstor for cstor in groupby if "cstor_name" in cstor["params"]]
                if len(groupby_cstor_name) == 0:
                    groupby.insert(0, {
                                    "params": [
                                    "cstor_name"
                                    ],
                                    "type": "tag"
                                    })
            # alias        
            alias = target["alias"]
            collector_tag = "" if is_on_demand else "(HKEx) "
            if "$tag_cstor_name" not in alias:
                if "$tag_" in alias:
                    tagIndex = alias.index("$tag_")
                    newAlias = alias[:tagIndex] + collector_tag + "$tag_cstor_name, " + alias[tagIndex:]
                else:
                    newAlias = collector_tag + "$tag_cstor_name"
            else:
                newAlias = alias.replace("$tag_cstor_name", collector_tag + "$tag_cstor_name")
            target["alias"] = newAlias
            # refId
            target["refId"] = QUERY_REFID_SEQUENCE[index]
            index = index + 1
            if not is_on_demand:
                # duplicate queries one per datasource, update datasource uid
                for new_ds in ds_mapped:
                    new_target = target.copy()
                    new_target["datasource"] = {
                                            "type": "influxdb",
                                            "uid": new_ds
                                            }
                    # if index == 25:
                    #     print('test')
                    new_target["refId"] = QUERY_REFID_SEQUENCE[index]
                    split_location = new_ds.index("_")
                    dc_name = new_ds[:split_location]
                    alias = new_target["alias"]
                    alias = alias.replace("HKEx", dc_name.upper())
                    new_target["alias"] = alias
                    duplicated_targets.append(new_target)
                    index = index + 1
        # add duplicated targets
        for nt in duplicated_targets:
            targets.append(nt)


def convert_variables(variables):
    if isinstance(variables, List):
        for index, variable in enumerate(variables):
            if variable["name"] == "cstor_name":
                update_cstor_name(variables[index])
            if variable["name"] == "cstor_ip":
                update_cstor_ip(variables[index])
            if variable["name"] == "network_monitor":
                variables.remove(variable)


def convert_panels(owner, panels, y_axis):
    new_panels = []
    index = 0
    for panel in panels:
        if panel["type"] == "row":
            gridPos = panel["gridPos"].copy()
            gridPos["y"] = y_axis
            y_axis = y_axis + gridPos["h"]
            panel["gridPos"] = gridPos
            if "panels" in panel:
                children = panel["panels"]
                convert_panels(panel, children, y_axis)
            new_panels.insert(index, panel)
            index = index + 1
        elif panel["type"] == "timeseries":
            update_graph_panel(panel)
            gridPos = panel["gridPos"].copy()
            gridPos["y"] = y_axis
            y_axis = y_axis + gridPos["h"]
            panel["gridPos"] = gridPos
            new_panels.insert(index, panel)
            index = index + 1
        elif panel["type"] == "cclear-ondemand-panel":
            ds = "flow_data_4_Tuple"
            if "TCP" in owner["title"]:
                ds = "tcp_4_Tuple"
            if "5 Tuple" in owner["title"]:
                ds = ds.replace("4", "5")
            # TODO: other analytics
            options = panel["options"]
            options["ltType"] = "Analytics, cStor and IP/CIDR "
            options["analyticsType"] = ds
            options["nmName"] = ""
            options["cStorName"] = "${cstor_name:raw}"
            # if "targets" in panel.keys():
            #     for target in panel["targets"]:
            #         target["datasource"] = {
            #                             "type": "mixed",
            #                             "uid": ds
            #                             }
            new_panels.insert(index, panel)
            index = index + 1
        elif panel["type"] == "table":
            ds_name = get_ds_name(panel["datasource"])
            ds_mapped = get_mapping_for_ds(ds_name)
            if ds_mapped:
                # check if contains on demand measurements
                is_on_demand = False
                targets = panel["targets"]
                for target in targets:
                    if "query" in target:
                        query = target["query"]
                        if any(ondemand in query for ondemand in ON_DEMAND_MEASUREMENTS):
                            is_on_demand = True
                            break
                # title
                if not is_on_demand:
                    panel["title"] = "(HKEx) " + panel["title"]
                # y axis
                gridPos = panel["gridPos"].copy()
                gridPos["y"] = y_axis
                y_axis = y_axis + gridPos["h"]
                panel["gridPos"] = gridPos
                # transform: assume only one "organize" transform per table
                if 'transformations' in panel.keys():
                    organize = [x for x in panel["transformations"] if x["id"] == "organize"]
                    if organize:
                        options = organize[0]["options"]
                        if "renameByName" in options:
                            options["renameByName"]["cstor_name"] = "cStor Name"
                        else:
                            options["renameByName"] = {"cstor_name": "cStor Name"}
                        if "indexByName" in options:
                            options["indexByName"]["cstor_name"] = 0
                        else:
                            options["indexByName"] = {"cstor_name": 0}
                        if "excludeByName" in options:
                            options["excludeByName"]["Time"] = True
                        else:
                            options["excludeByName"] = {"Time": True}
                # url cstor name: "fieldConfig"."overrides".listItem: "properties".listItem: {"id": "links", "values": [..., "url"]
                if not is_on_demand:
                    overrides = panel["fieldConfig"]["overrides"]
                    for override in overrides:
                        properties = override["properties"]
                        for prop in properties:
                            if prop["id"] == "links":
                                values = prop["value"]
                                for value in values:
                                    url = value["url"]
                                    if url:
                                        new_url = re.sub("var\-cstor_name=\$\{cstor_name\:text\}","var-cstor_name=All", url)
                                        new_url = re.sub("var\-cstor_name=\$\{cstor_name\}","var-cstor_name=All", new_url)
                                        new_url = re.sub("var\-cstor_name=\$cstor_name","var-cstor_name=All", new_url)
                                        new_url = re.sub("var\-cstor_ip=\$\{cstor_ip\:text\}","var-cstor_ip=All", new_url)
                                        new_url = re.sub("var\-cstor_ip=\$\{cstor_ip\}","var-cstor_ip=All", new_url)
                                        new_url = re.sub("var\-cstor_ip=\$cstor_ip","var-cstor_ip=All", new_url)
                                        value["url"] = new_url
        
                new_panels.insert(index, panel)
                index = index + 1

                if not is_on_demand:
                    for new_ds in ds_mapped:
                        new_panel = panel.copy()
                        # title
                        split_location = new_ds.index("_")
                        dc_name = new_ds[:split_location]
                        title = new_panel["title"]
                        title = title.replace("HKEx", dc_name.upper())
                        new_panel["title"] = title
                        # y axis
                        gridPos = new_panel["gridPos"].copy()
                        gridPos["y"] = y_axis
                        y_axis = y_axis + gridPos["h"]
                        new_panel["gridPos"] = gridPos
                        # datasource
                        new_panel["datasource"] =  {
                                                "type": "influxdb",
                                                "uid": new_ds
                                                }
                        targets = new_panel["targets"]
                        for target in targets:
                            target["datasource"] =  {
                                                "type": "influxdb",
                                                "uid": new_ds
                                                }
                        # panel position in order
                        new_panels.insert(index, new_panel)
                        index = index + 1
        else:
            gridPos = panel["gridPos"].copy()
            gridPos["y"] = y_axis
            y_axis = y_axis + gridPos["h"]
            panel["gridPos"] = gridPos
            new_panels.insert(index, panel)
            index = index + 1
    owner["panels"] = new_panels


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
            converted_dashboards.append((GlobalMergedCollectorConverter.from_object(dash_obj), file))
            return converted_dashboards
    
    @staticmethod
    def from_object(dash_obj: Dict) -> Dict:
        if not dash_obj: 
            raise DashboardTransformError('The dashboard to convert is empty. Please check the passed in dashboard.')
        remove_nm_dash(dash_obj)
        if 'templating' in dash_obj.keys():
            variables = dash_obj["templating"]["list"]
            convert_variables(variables)
        if 'panels' in dash_obj.keys():
            panels = dash_obj["panels"]
            convert_panels(dash_obj, panels, 0)
        # TODO: fix the temparory always True
        return dash_obj

if __name__ == '__main__':
  pass
