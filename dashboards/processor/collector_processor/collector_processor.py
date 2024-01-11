from typing import Dict, List, Optional, Tuple
from dashboards.processor.collector_processor.collector_config import CollectorConfigs
from dashboards.processor.collector_processor.merged_collectors_processor import MergedCollectorsProcessor
from dashboards.processor.collector_processor.per_collector_processor import PerCollectorProcessor
from dashboards.processor.dashboard_processor import AbstractProcessor


class CollectorProcessor(AbstractProcessor):

    def __init__(self, config_file: str, glogal_uids: List[str], collector_uids: List[str]):
        # config
        self._collector_configs = CollectorConfigs(config_file, glogal_uids, collector_uids)
        # converters
        self._merged_converter = MergedCollectorsProcessor(self._collector_configs)
        self._collector_converter = PerCollectorProcessor(self._collector_configs)

    # override
    def process_dashboard(self, dashboard: Dict, key = None) -> Optional[List[Tuple[Dict, Optional[str]]]]:    # [(dashboard, <key>|None)]
        # convert
        merged = self._merged_converter.process_dashboard(dashboard, key)
        per_collector = self._collector_converter.process_dashboard(dashboard, key)
        # return combined results
        if merged and per_collector:
            return merged + per_collector
        return merged if merged else per_collector
        
