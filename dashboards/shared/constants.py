LOGICAL_OR = 'OR'
LOGICAL_AND = 'AND'
#
DS_INDICATORS = {"type": "influxdb", "uid": "indicators"}
DS_IGNORED = ("grafana", "mixed", "dashboard")
KEY_DATASOURCE = "datasource"
KEY_TITLE = "title"
KEY_UID = "uid"
OPTIONS_DEFAULT_ALL = {"selected": True, "text": ["All"], "value": ["$__all"]}
OPTIONS_DEFAULT_NONE = {"selected": False, "text": [""], "value": [""]}
DATASOURCE_MIXED = {"type": "mixed", "uid": "-- Mixed --"}
ON_DEMAND_MEASUREMENTS = (
    "flow_data_4_Tuple",
    "flow_data_5_Tuple",
    "tcp_4_tupe",
    "tcp_5_Tuple",
)
# define Tuple with char A-Z
QUERY_REFID_SEQUENCE = tuple(chr(i) for i in range(65, 91))
