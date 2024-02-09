import json
import os
import re
from typing import Dict, List, Optional, Tuple


class Database:
    def __init__(self, schema_config: str) -> None:
        if not schema_config or not os.path.exists(schema_config):
            raise Exception(f'Schema config not specified or does not exist: {schema_config}')
        if os.path.isfile(schema_config) and not (os.path.basename(schema_config).endswith('.json') or os.path.basename(schema_config).endswith('.jsonc')):
            raise Exception(f'File specified is not a dashboard .json file: {schema_config}')
        with open(schema_config, 'r') as f:
            content = f.read()
            content = re.sub(r'//.*?\n|/\*.*?\*/', '', content, flags=re.S)
            self._schema: Dict = json.loads(content)

    def _find_measurements(self, key, tags: Dict) -> Optional[List[Tuple[str, List[str]]]]:
        measurements: List[Tuple[str, List[str]]] = list()
        for m, m_tags in tags.items():
            found_tags: List[str] = list()
            keys = m_tags['keys']
            found = False
            for _key, vallues in keys.items():
                for value in vallues:
                    if key.lower() == value.strip().lower():
                        found_tags.append(_key)
                        found = True
                        break
            if found:
                measurements.append((m, found_tags))
        return measurements

    def _from_timeslice(self, metric, tag) -> Optional[Tuple[Optional[List[Tuple[str, List[str]]]], Optional[List[str]]]]:
        fields: List[str] = self._schema["timeslice"]["fields"]
        if metric not in fields:
            return None
        schema = self._find_measurements(tag, self._schema["timeslice"]["measurements"])
        return (schema, self._schema['timeslice']['ip_measurements'])

    def _from_open(self, metric, tag) -> Optional[Tuple[Optional[List[Tuple[str, List[str]]]], Optional[List[str]]]]:
        fields: List[str] = self._schema["open"]["fields"]
        if metric not in fields:
            return None
        schema = self._find_measurements(tag, self._schema["open"]["measurements"])
        return (schema, self._schema['open']['ip_measurements'])
        
    def get_schema(self, metrics: List[str], tag_key, filter = None) -> Dict[str, Tuple[Optional[List[Tuple[str, List[str]]]], Optional[List[str]]]]:
        """
        Collect measurement, tags for request
        """
        schema: Dict[str, Tuple[Optional[List[Tuple[str, List[str]]]], Optional[List[str]]]] = dict()
        for metric in metrics:
            # locate metric in schema
            m = self._from_timeslice(metric, tag_key)
            if not m:
                m = self._from_open(metric, tag_key)
            if not m:
                print(f'WARNING: no matching measurement found for metric {metric} and tag {tag_key}.')
                continue
            schema[metric] = m
        return schema
    