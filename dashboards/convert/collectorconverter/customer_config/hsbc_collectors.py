
from typing import Dict, Tuple

# global cclear: local collector
LOCAL_COLLECTOR_KEY = 'hkex'
LOCAL_COLLECTOR_LABEL = 'HKEx'
# remote collector 1: hk3
HK3_KEY = 'hk3'
HK3_LABEL = 'HK3'
HK3_LABEL_MAPPING: Dict[str, str] = {LOCAL_COLLECTOR_LABEL: HK3_LABEL}
HK3_DS_MAPPING: Dict[str, str] = {'applications': f'{HK3_KEY}_applications', 
                    'dhcp': f'{HK3_KEY}_dhcp', 
                    'dns': f'{HK3_KEY}_dns', 
                    'flows': f'{HK3_KEY}_flows',
                    'https': f'{HK3_KEY}_https',
                    'icmp': f'{HK3_KEY}_icmp',
                    'indicators': f'{HK3_KEY}_indicators',
                    'tcp': f'{HK3_KEY}_tcp',
                    'ip_map': f'{HK3_KEY}_ip_map',
                    'sys': f'{HK3_KEY}_sys',
                    'influxdb_health': f'{HK3_KEY}_influxdb_health'}
# remote collector 2: fdc2
FDC2_KEY = 'fdc2'
FDC2_LABEL = 'FDC2'
FDC2_LABEL_MAPPING: Dict[str, str] = {LOCAL_COLLECTOR_LABEL: FDC2_LABEL}
FDC2_DS_MAPPING: Dict[str, str] = {'applications': f'{FDC2_KEY}_applications', 
                    'dhcp': f'{FDC2_KEY}_dhcp',
                    'dns': f'{FDC2_KEY}_dns', 
                    'flows': f'{FDC2_KEY}_flows', 
                    'https': f'{FDC2_KEY}_https', 
                    'icmp': f'{FDC2_KEY}_icmp', 
                    'indicators': f'{FDC2_KEY}_indicators', 
                    'tcp': f'{FDC2_KEY}_tcp',
                    'ip_map': f'{FDC2_KEY}_ip_map',
                    'sys': f'{FDC2_KEY}_sys',
                    'influxdb_health': f'{FDC2_KEY}_influxdb_health'}

# collector mapping data structure to pass to the converters
COLLECTOR_MAPPINGS: Dict[str,Tuple[Dict[str, str], Dict[str, str]]] = {HK3_KEY: (HK3_LABEL_MAPPING,  HK3_DS_MAPPING), FDC2_KEY: (FDC2_LABEL_MAPPING,FDC2_DS_MAPPING)}

