from typing import Dict, List, Optional, Tuple
from dashboards.shared.constants import DS_IGNORED
from dashboards.shared.commons import DashboardTransformError
from dashboards.convert.collectorconverter.customer_config.hsbc_collectors import COLLECTOR_MAPPINGS

FOLDERS_WITH_MERGED_GLOBAL_DASHBOARDS = {'flow_analytics', 'tcp_analytics', 'ip_troubleshooting', 'custom'}
FOLDERS_WITH_SEPARATE_GLOBAL_DASHBOARDS = {'application_analytics', 'debug', 'devices', 'system'}
COPY_FORWARD_ORIGINAL = False
OUTPUT_FOLDER_PER_COLLECTOR = True
# TODO
COLLECTOR_DS_MAPPINGS_FROM_GRAFANA = False
CREATE_DS_FOR_COLLECTORS = False


def get_mapping_for_ds(ds_original: str) -> Optional[List[str]]:
    if not ds_original or len(ds_original) == 0:
        return None
    if any(ds in ds_original.lower() for ds in DS_IGNORED):
        return None
    ds_mapping: List[str] = []
    try:
        for collector_mapping in COLLECTOR_MAPPINGS.values():
            ds = collector_mapping[1].get(ds_original, None)
            if not ds:
                raise DashboardTransformError(f'Could not find mapping value for datasource {ds_original}. May need to create a mapping datasource for this.')
            ds_mapping.append(ds)
    except KeyError as ke:
        raise DashboardTransformError(f'Could not find mapping value for datasource {ds_original}. May need to create a mapping datasource for this. Nested KeyError: {ke}')
    return ds_mapping

def get_ds_mappings_from_grafana() -> Dict[str,Tuple[str, Dict[str, str]]]:
    """ TODO: make API calls to grafana instance and gather """
    return {}