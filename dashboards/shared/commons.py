from abc import ABC, abstractmethod
import re
from typing import Callable, Dict, List, Optional, Tuple

from dashboards.shared.constants import ON_DEMAND_MEASUREMENTS

# TODO: validate ds_name is within known list
def create_new_influxdb_datasource(ds_name: str) -> Dict:
    datasource: Dict = {
                        "type": "influxdb",
                        "uid": ds_name
                        }
    return datasource

def get_ds_name(datasource) -> str:
    if isinstance(datasource, Dict):
        return datasource["uid"]
    else:
        return datasource


def replace_key_list(
    dash_element: Dict, child_key: str, mappings: List[Tuple[str, str]]
) -> Dict:
    for mapping in mappings:
        replace_key(dash_element, child_key, mapping)
    return dash_element


def replace_key(dash_element: Dict, child_key: str, mapping: Tuple[str, str]) -> Dict:
    if child_key not in dash_element.keys():
        return dash_element
    match_key = dash_element[child_key]
    key, value = mapping
    if key in match_key.keys():
        match_key[value] = match_key.pop(key)
    return dash_element


def replace_value_str_list(
    dash_element: Dict, child_keys: List, mappings: List[Tuple[str, str]]
) -> Dict:
    for child_key in child_keys:
        if child_key in dash_element.keys():
            for key, value in mappings:
                dash_element = replace_value_str(dash_element, child_key, (key, value))
    return dash_element


def replace_value_str(
    dash_element: Dict, child_key: str, mapping: Tuple[str, str]
) -> Dict:
    if child_key not in dash_element.keys():
        return dash_element
    match, sub = mapping
    str_original = dash_element[child_key]
    if isinstance(str_original, str):
        dash_element[child_key] = re.sub(match, sub, str_original)
    return dash_element

def node_remove_from_nested_dict_by_keys(dict_to_remove_from: Dict, match_key_parent: str, match_key_child: str) -> Dict:
    if match_key_parent in dict_to_remove_from.keys():
        value = dict_to_remove_from[match_key_parent]
        if isinstance(value, Dict) and match_key_child in value.keys():
            del value[match_key_child]
    return dict_to_remove_from

def node_remove_from_dict_by_key(dict_to_remove_from: Dict, key_to_remove: str) -> Dict:
    if key_to_remove in dict_to_remove_from.keys():
        del dict_to_remove_from[key_to_remove]
    return dict_to_remove_from

# Dict->List->Dict[key] = match
def node_remove_from_list_by_match(list_to_remove_from: Dict[str, List], match_key: str, match_for_removal: List[Tuple[Optional[str], Callable[[str, str], bool], str]]) -> Tuple[Dict, bool]:
    if match_key in list_to_remove_from.keys():
        value = list_to_remove_from[match_key]
        if isinstance(value, List):
            is_deleted = False
            for item in value:
                if isinstance(item, Dict):
                    # construct matching condition, search and remove
                    match_expression_or = False
                    for key, op, match in match_for_removal:
                        if key:
                            match_expression_or = match_expression_or or op(item[key], match)
                        else:
                            match_expression_or = match_expression_or or op(str(item), match)
                    if match_expression_or:
                        value.remove(item)
                        is_deleted = True
            return list_to_remove_from, is_deleted
    return list_to_remove_from, False

# url cstor name: "fieldConfig"."overrides".listItem: "properties".listItem: {"id": "links", "values": [..., "url"]
def overrides_update_links(override_element: List[Dict], mappings: List[Tuple[str, str]]) -> List[Dict]:
    if not isinstance(override_element, List):
        return override_element
    for override in override_element:
        if isinstance(override, Dict) and "properties" in override.keys():
            properties = override["properties"]
            for prop in properties:
                if prop["id"] == "links":
                    values = prop["value"]
                    for value in values:
                        key = 'url'
                        if value[key]:
                            for match, sub in mappings:
                                replace_value_str(value, key, (match, sub))
    return override_element

def leaf_node_replace(dash_element: Dict, key: str, match: Optional[str|bool|int|float], sub: Optional[str|bool|int|float]) -> Dict:
    if  not isinstance(dash_element, Dict) or key not in dash_element.keys():
        return dash_element
    value = dash_element[key]
    if isinstance(value, Dict) or isinstance(value, List):
        return dash_element
    if isinstance(match, str):
        dash_element[key] = re.sub(match, str(sub), value)
    else:
        dash_element[key] = sub
    return dash_element

def query_add_tag_to_groupby(target_element: Dict, tag_name_to_add: str, query_pattern_spot_to_add: str, alias_label: str) -> Dict:
    if not isinstance(target_element, Dict):
        return target_element
    # add cstor_name to query
    if "query" in target_element and 'rawQuery' in target_element.keys() and target_element['rawQuery']:
        query = target_element["query"]
        # add cstor_name to groupby
        if not re.search(query_pattern_spot_to_add, query):
            if "fill" in query:
                fillIndex = query.rindex("fill")
                query = f'{query[:fillIndex]}, "{tag_name_to_add}" {query[fillIndex:]}'
            else:
                query = f'{query}, "{tag_name_to_add}"'
        target_element["query"] = query
    # add cstor_name to groupby
    if "groupBy" in target_element.keys():
        groupby = target_element["groupBy"]
        groupby_cstor_name = [cstor for cstor in groupby if tag_name_to_add in cstor["params"]]
        if len(groupby_cstor_name) == 0:
            groupby.insert(0, {
                            "params": [
                            tag_name_to_add
                            ],
                            "type": "tag"
                            })
    # add alias for cstor_name
    alias = target_element["alias"]
    collector_tag = alias_label
    if f'$tag_{tag_name_to_add}' not in alias:
        if "$tag_" in alias:
            tagIndex = alias.index("$tag_")
            newAlias = f'{alias[:tagIndex]}{collector_tag}"$tag_{tag_name_to_add}, " {alias[tagIndex:]}'
        else:
            newAlias = f'{collector_tag} "$tag_{tag_name_to_add}"'
    else:
        newAlias = alias.replace(f'"$tag_{tag_name_to_add}"', f'{collector_tag}"$tag_{tag_name_to_add}"')
    target_element["alias"] = newAlias
    return target_element

class DashboardTransformError(Exception):
    """Exception raised for errors in the division."""

    def __init__(self, message):
        self.message = message


class AbstractDashboardEditor(ABC):
    @staticmethod
    @abstractmethod
    def from_file(
        file: str, key: Optional[str] = None
    ) -> Optional[List[Tuple[Dict, Optional[str]]]]:
        raise NotImplementedError
