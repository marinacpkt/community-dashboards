#  Create dashboards on the fly

Refer to: https://grafana.com/docs/grafana/latest/dashboards/build-dashboards/view-dashboard-json-model/

The goal is to:
* Create dashboards according to config:
    * Create Host Group workflow of dashboards only when hosts group are configured: add a config variable for both the collector and the dashboards...before that, let users select which ones at their preference
    * Create Custom Application workflow of dashboards only when Custom Applications are configured: add a config variable for both the collector and the dashboards...before that, let users select which ones at their preference
    * Create Network Monitor workflow of dashboards for network monitors with a smaller CIDR
    * Create global cClear dashboards for selected options and configs
    * Create other dashboards at request
    * ...
* Add a link to the plugin from home page to go and add more dashboard anytime