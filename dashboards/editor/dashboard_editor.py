import re
from typing import Any, Callable, Dict, List, Optional, Tuple

LOGICAL_OR = 'OR'
LOGICAL_AND = 'AND'

class DashboardTransformError(Exception):
    """Exception raised for errors in the division."""

    def __init__(self, message):
        self.message = message


# TODO: validate ds_name is within known list
def create_new_influxdb_datasource(ds_name: str) -> Dict:
    datasource: Dict = {"type": "influxdb", "uid": ds_name}
    return datasource


def get_ds_name(datasource) -> str:
    if isinstance(datasource, Dict):
        return datasource["uid"]
    else:
        return datasource

# ------------------- dict_list_<item>(str|bool|int|float) ------------------------
# dict_list_<item>(str|bool|int|float)
def dict_list_item__replace_str(dict_owner: dict, match_key, search_replace: List[Tuple[str, str]]):
    if isinstance(dict_owner, dict) and match_key in dict_owner.keys():
        element_list = dict_owner[match_key]
        if isinstance(element_list, list):
            for item in element_list:
                if isinstance(item, str|bool|int|float):
                    for search, replace in search_replace:
                        if search:
                            for index, item in enumerate(element_list):
                                element_list[index] = re.sub(search, replace, item)

# dict_list_<item>(str|bool|int|float)
def dict_list_item__delete_item_str(dict_owner: dict, match_key, matches: List[Tuple[Callable[[str, str], bool], str]]): # expression: [OP, b]
    if isinstance(dict_owner, dict) and match_key in dict_owner.keys():
        element_list = dict_owner[match_key]
        if isinstance(element_list, list):
            indices: List[int] = list()
            for index, item in enumerate(element_list):
                if isinstance(item, str|bool|int|float):
                    for op, match in matches:
                        if op(str(item), str(match)):
                            indices.append(index)
            for index in indices:
                element_list.remove(index)

# ------------------- dict_dict_<item>(str|bool|int|float) ------------------------
def dict_dict_item__replace_key_list(
    element: Dict, key, mappings: List[Tuple[str, str]]
) -> Dict:
    for mapping in mappings:
        dict_dict__replace_key(element, key, mapping)
    return element

def dict_dict__replace_key(element: Dict, key, mapping: Tuple[str, str]) -> Dict:
    if not isinstance(element, Dict):
        return element
    if key not in element.keys():
        return element
    match_key = element[key]
    key, value = mapping
    if key in match_key.keys():
        match_key[value] = match_key.pop(key)
    return element

# ------------------- dict_<item>(key:value<str|bool|int|float>) ------------------------
def dict_item__replace_value_str_list(
    element: Dict, keys: List, mappings: List[Tuple[str, str]]
) -> Dict:
    if not isinstance(element, Dict):
        return element
    for key in keys:
        if key in element.keys():
            for mapping in mappings:
                element = dict_item__replace_value_str(element, key, mapping)
    return element

# key: value(str|bool|int|float)
def dict_item__replace_value_str(element: Dict, key, mapping: Tuple[str, str]) -> Dict:
    if not isinstance(element, Dict):
        return element
    if key not in element.keys():
        return element
    match, sub = mapping
    str_original = element[key]
    if isinstance(str_original, str):
        element[key] = re.sub(match, sub, str_original)
    # else:
        # element[key] = sub
        # print(f"element[key] is not a string: {element[key]}, key: {key}, mapping: {mapping}, element: {element}")
    return element

 # ------------------- dict_dict_<item> operations ------------------------
# dict_dict_<item>. Examples:
# dict_dict_item__delete_item_by_key(dash_element, 'excludeByName', 'network_monitor_name')
# dict_dict_item__delete_item_by_key(dash_element, 'fields', 'network_monitor_name')
# dict_dict_item__delete_item_by_key(dash_element, 'fields', 'Network Monitor')
# dict_dict_item__delete_item_by_key(dash_element, 'indexByName', 'network_monitor_name')
# dict_dict_item__delete_item_by_key(dash_element, 'renameByName', 'network_monitor_name')
def dict_dict__delete_item_by_key(
    dict_to_remove_from: Dict, match_key_parent, match_key_child: str
) -> Dict:
    if match_key_parent in dict_to_remove_from.keys():
        value = dict_to_remove_from[match_key_parent]
        if isinstance(value, Dict) and match_key_child in value.keys():
            del value[match_key_child]
    return dict_to_remove_from

def dict__delete_item_by_key(dict_to_remove_from: Dict, key_to_remove: str) -> Dict:
    if key_to_remove in dict_to_remove_from.keys():
        del dict_to_remove_from[key_to_remove]
    return dict_to_remove_from

def dict_dict_item__delete_item_by_key_value(dict_owner: dict, owner_key, match: Tuple[str, Any]):
    if owner_key and dict_owner and isinstance(dict_owner, dict) and owner_key in dict_owner.keys():
        element_dict = dict_owner[owner_key]
        if isinstance(element_dict, Dict) and match:
            for key, value in match:
                if element_dict[key] == value:    # match
                    del element_dict[key]

# dict_list_<item>(str|bool|int|float)
def dict_list__delete_item_str(dict_owner: dict, match_key, matches: List[Tuple[Callable[[str, str], bool], str]]): # expression: [OP, b]
    if isinstance(dict_owner, dict) and match_key in dict_owner.keys():
        element_list = dict_owner[match_key]
        if isinstance(element_list, list):
            indices: List[int] = list()
            for index, item in enumerate(element_list):
                if isinstance(item, str|bool|int|float):
                    for op, match in matches:
                        if op(str(item), str(match)):
                            indices.append(index)
            for index in indices:
                element_list.remove(index)

# dict_list_<item>(dict by match). Examples:
# dict_list_item__delete_item_dict(dash_element, 'list', [(OPERAND_OR, 'name', operator.eq, 'network_monitor')])
# dict_list_item__delete_item_dict(dash_element, 'groupBy', [(OPERAND_OR, 'params', operator.contains, 'network_monitor_name'), (OPERAND_OR, 'params',operator.contains, 'network_monitor'), (OPERAND_OR, 'params',operator.contains, 'network_monitor_name::tag')])
# dict_list_item__delete_item_dict(dash_element, 'select', [(OPERAND_OR, 'params', operator.contains, 'network_monitor_name'), (OPERAND_OR, 'params',operator.contains, 'network_monitor')])
# dict_list_item__delete_item_dict(dash_element, 'fields', [(OPERAND_OR, None, operator.contains, '(?i)network\s+(?i)monitor')])
# dict_list_item__delete_item_dict(templating, 'list', [('OR', 'name', operator.eq, 'network_monitor')])
def dict_list__delete_item_dict(dict_list_owner: Dict[str, List], match_key: str, match_expressions: List[Tuple[Optional[str], Optional[str], Callable[[str, str], bool], str]]):
    if dict_list_owner and isinstance(dict_list_owner, dict) and match_key:
        if match_key in dict_list_owner.keys():
            value = dict_list_owner[match_key]
            if isinstance(value, List):
                for item in value:
                    if isinstance(item, Dict):
                        if not match_expressions or len(match_expressions) == 0:
                            del dict_list_owner[match_key]
                        else:
                            match_expression =  dict_resolve_expression(item, None, match_expressions[0])
                            for expression in match_expressions:
                                match_expression = dict_resolve_expression(item, match_expression, expression)
                            if match_expression:
                                value.remove(item)

# element: dict
def dict_resolve_expression(element: Dict, prev: Optional[bool], expression: Tuple[Optional[str], Optional[str], Callable[[str, str], bool], str]) -> bool:
    logical_operator, key, op, match = expression
    if not prev:
        if key:
                return op(element[key], match)
        else:
            return op(str(element), match)
    else:
        if key:
            if not logical_operator or logical_operator.strip().upper() == LOGICAL_OR:
               return prev or op(element[key], match)
            else:
                return prev and op(element[key], match)
        else:
            if not logical_operator or logical_operator.strip().upper() == LOGICAL_OR:
               return prev or op(str(element), match)
            else:
                return prev and op(str(element), match)


 # ------------------- dict_<item>(any) operations ------------------------
# dict_<item>(any)
def dict_item__edit_item_by_match(dict_owner: Dict, match: Tuple[str, Any], items: List[Tuple[str, Any]]):
    if dict_owner and isinstance(dict_owner, Dict) and items and len(items) > 0:
        match_key, match_value = match
        if match_key in dict_owner.keys() and dict_owner[match_key] == match_value:
            for key, value in items:
                dict_owner[key] = value

# url cstor name: "fieldConfig"."overrides".listItem: "properties".listItem: {"id": "links", "values": [..., "url"]
def overrides_update_links(
    override_element: List[Dict], mappings: List[Tuple[str, str]]
) -> List[Dict]:
    if not isinstance(override_element, List):
        return override_element
    for override in override_element:
        if isinstance(override, Dict) and "properties" in override.keys():
            properties = override["properties"]
            for prop in properties:
                if prop["id"] == "links":
                    values = prop["value"]
                    for value in values:
                        key = "url"
                        if value[key]:
                            for match, sub in mappings:
                                dict_item__replace_value_str(value, key, (match, sub))
    return override_element


def query_add_tag_to_groupby(
    target_element: Dict,
    tag_name_to_add,
    query_pattern_spot_to_add,
    alias_label,
) -> Dict:
    if not isinstance(target_element, Dict):
        return target_element
    # add cstor_name to query
    if (
        "query" in target_element
        and "rawQuery" in target_element.keys()
        and target_element["rawQuery"]
    ):
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
        groupby_cstor_name = [
            cstor for cstor in groupby if tag_name_to_add in cstor["params"]
        ]
        if len(groupby_cstor_name) == 0:
            groupby.insert(0, {"params": [tag_name_to_add], "type": "tag"})
    # add alias for cstor_name
    alias = target_element["alias"]
    collector_tag = alias_label
    if f"$tag_{tag_name_to_add}" not in alias:
        if "$tag_" in alias:
            tagIndex = alias.index("$tag_")
            newAlias = f'{alias[:tagIndex]}{collector_tag}"$tag_{tag_name_to_add}, " {alias[tagIndex:]}'
        else:
            newAlias = f'{collector_tag} "$tag_{tag_name_to_add}"'
    else:
        newAlias = alias.replace(
            f'"$tag_{tag_name_to_add}"', f'{collector_tag}"$tag_{tag_name_to_add}"'
        )
    target_element["alias"] = newAlias
    return target_element
