
# Organize dashboard for conversion among them
# hosts group
KEY_HOSTS_GROUP = 'key_hosts_group'
LABEL_HOSTS_GROUP = ['Hosts Group']
SCHEMA_TAG_HOSTS_GROUP = 'hosts_group'
# custom application
KEY_CUSTOM_APPLICATION = 'key_custom_application'
LABEL_CUSTOM_APPLICATION = ['Custom Application', 'Application']
SCHEMA_TAG_CUSTOM_APPLICATION = 'custom_application'
# sni name
KEY_TLS_DOMAIN = 'key_tls_domain'
LABEL_TLS_DOMAIN = ['SNI Name']
SCHEMA_TAG_TLS_DOMAIN = 'tls_domain'
# cname
KEY_CNAME_DOMAIN = 'key_cname_domain'
LABEL_CNAME_DOMAIN = ['Canonical Name']
SCHEMA_TAG_CNAME_DOMAIN = 'cname_domain'
DASHBOARD_SETS_APPLICATIONS = {KEY_HOSTS_GROUP: (LABEL_HOSTS_GROUP, SCHEMA_TAG_HOSTS_GROUP),
                               KEY_CUSTOM_APPLICATION: (LABEL_CUSTOM_APPLICATION, SCHEMA_TAG_CUSTOM_APPLICATION),
                               KEY_TLS_DOMAIN: (LABEL_TLS_DOMAIN, SCHEMA_TAG_TLS_DOMAIN),
                               KEY_CNAME_DOMAIN: (LABEL_CNAME_DOMAIN, SCHEMA_TAG_CNAME_DOMAIN)}
#
DS_IGNORED = ('grafana', 'mixed', 'dashboard')
KEY_DATASOURCE ='datasource'
KEY_TITLE = 'title'
KEY_UID = 'uid'
CUSTOM_OPTIONS_DEFAULT_ALL = {
        "selected": "true",
          "text": [
            "All"
          ],
          "value": [
            "$__all"
          ]
        }
DATASOURCE_MIXED = {
                    "type": "mixed",
                    "uid": "-- Mixed --"
                   }
ON_DEMAND_MEASUREMENTS = ("flow_data_4_Tuple", "flow_data_5_Tuple", "tcp_4_tupe", "tcp_5_Tuple")
# define Tuple with char A-Z
QUERY_REFID_SEQUENCE =  tuple(chr(i) for i in range(65, 91))

