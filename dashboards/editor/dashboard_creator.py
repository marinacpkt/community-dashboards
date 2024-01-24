
import copy
import json
import os
from pathlib import Path
import re
import uuid

from dotenv import load_dotenv
import requests
from dashboards.editor.database import Database
from typing import Dict, List, Optional, Tuple, Any


WHERE = "WHERE $timeFilter"
GROUPBY = "GROUP BY time($interval)"

def update_panel_position_y(position_element: Dict, current_posion_y: int) -> Tuple[Dict, int]:
    gridPos = position_element.copy()
    gridPos["y"] = current_posion_y
    next_position_y = current_posion_y + gridPos["h"]
    return gridPos, next_position_y

class DashboardCreator:
    def __init__(self, db: Database) -> None:
        self._db = db

    def _get_dashboard_schema(self) -> Dict[str, Any]:
        file = "/Users/mzheng/Work/community-dashboards/dashboards/schema/dashboard.schema.json"
        with open(file, 'r') as f:
            schema = json.load(f)
        return schema
    
    def _get_dashboard_template(self) -> Dict[str, Any]:
        file = "/Users/mzheng/Work/community-dashboards/dashboards/schema/elements/template_dashboard.json"
        with open(file, 'r') as f:
            dashboard = json.load(f)
        return dashboard

    def create(self, metrics: List[str], tag_key, filter = None):
        measurements: Dict[str, Tuple[Optional[List[Tuple[str, List[str]]]], Optional[List[str]]]] = self._db.get_schema(metrics, tag_key, filter)  
        dashboard: Optional[Dict] = self.create_dashboard(tag_key, measurements, filter)
        # if dashboard:
        #     with open("/Users/mzheng/Work/community-dashboards/dashboards/editor/new_dashboard.json", "w") as f:
        #         json.dump(dashboard, f, indent=2)
        #         f.write('\n')
        # TODO
        # call Grafana API to create dashboard
        if dashboard:
            self.push_dashboard(dashboard)
        # return dashboard link
    
    def push_dashboard(self, dashboard: Dict) -> None:
        # print('Load dotenv: ', load_dotenv(dotenv_path=Path("env")))
        self.__USER = os.getenv("GRAFANA_USER")
        self.__PW = os.getenv("GRAFANA_PW")
        if not self.__USER or not self.__PW:
            raise Exception('Grafana GRAFANA_USER and GRAFANA_PW not set in env file')
        self.host_ip = "10.51.10.204"
        self.folder_id = 466
        self.dashboard = dashboard
        self.overwrite = False
        self.url = f'https://{self.__USER}:{self.__PW}@{self.host_ip}/graph-engine/api/dashboards/db'
        post_data = {
            # 'folderID': self.folder_id
                     "folderUid": "a412efba-d02d-41b0-8afc-57670464b375"
                     , 'dashboard': self.dashboard
                     , "message": f"Upload of {self.dashboard['title']}"
                     , "overwrite": self.overwrite}
        
        headers = {'Content-type': 'application/json'}
        response = requests.post(url=self.url
                                , data=json.dumps(post_data)
                                , headers=headers
                                , verify=False)
        print(response.status_code)
        print(response.text)
    
    def create_dashboard(self, key, measurements: Dict[str, Tuple[Optional[List[Tuple[str, List[str]]]], Optional[List[str]]]], filter = None) -> Optional[Dict]:
        """
        Create dashboard from measurements.
        """
        if not measurements:
            return None
        # dashboard
        dashboard: Dict = self._get_dashboard_template()
        dashboard['title'] = key
        dashboard['panels'][2]['title'] = f'{key} {": "+ filter if filter else ""}'
        dashboard['uid'] = uuid.uuid4().hex
        # panels
        schema = self._get_dashboard_schema()
        template_panel: Dict = schema['graph']
        panels: List[Dict] = dashboard['panels']
        next_panel_id: int = 5
        next_pos_y: int = 5
        for metric, s in measurements.items():
            m, ip_m = s
            # start of one panel per metric and measurement
            for measurement in m: # type: ignore
                m_name, m_tag = measurement
                # groupby, where (filter) tags and alias tags
                arr_alias: List[str] = list()
                arr_where: List[str] = list()
                arr_groupy: List[str] = list()
                for tag in m_tag:
                    arr_groupy.append(f'"{tag}"')
                    arr_alias.append(f'$tag_{tag}')
                    if filter:
                        arr_where.append(f'"{tag}" =~ /^{filter}$/')
                    else:
                        name = re.sub(" ", "_", key)
                        arr_where.append(f'"{tag}" =~ /^${name}$/')
                groupby_sql = ', '.join(arr_groupy)
                where_sql = ' Or '.join(arr_where)
                where_sql = f' AND ({where_sql})' if where_sql else ''
                alias_sql = ','.join(arr_alias)
                sql = f'SELECT sum("{metric}") FROM "{m_name}" {WHERE} {where_sql} {GROUPBY}, {groupby_sql} fill(none)'
                # create panel
                new_panel: Dict = copy.deepcopy(template_panel)
                if filter:
                    new_panel['title'] = f'{m_name} - "{metric}" with {where_sql[4:]}'
                else:
                    new_panel['title'] = f'{m_name} - "{metric}" by {groupby_sql}'
                new_panel['id'] = next_panel_id
                next_panel_id += 1
                new_panel["gridPos"], next_pos_y  = update_panel_position_y(new_panel['gridPos'], next_pos_y)
                target: Dict = new_panel['targets'][0]
                target['alias'] = alias_sql
                target['query'] = sql
                panels.append(new_panel)
            # filter with ip
            if filter:
                if self._is_ip_dashboard(measurements):
                    ondemand_panels: List[Dict] = schema['ondemand']
                    ondemand_panels[0]['options']['cidr'] = filter
                    # graph panel
                    where_on_demand = f'AND ("client_ip" =~ /^${filter}$/ OR "server_ip" =~ /^${filter}$/)'
                    ondemand_panels[1]['title'] = f'Client <-> Server - {metric}'
                    graph_targets = ondemand_panels[1]['targets']
                    graph_targets[0]['query'] = f'SELECT sum("{metric}") FROM "tcp_timeslice_4_tuple" {WHERE} {where_on_demand} {GROUPBY}, {groupby_sql} fill(none)'
                    graph_targets[1]['query'] = f'SELECT sum("{metric}") FROM "tcp_open_4_tuple" {WHERE} {where_on_demand} {GROUPBY}, {groupby_sql} fill(none)'
                    # timeslice table
                    ondemand_panels[2]['title'] = f'Timeslice: Client <-> Server - {metric}'
                    ondemand_panels[2]['targets'][0]['query'] = f'SELECT sum("{metric}") FROM "tcp_timeslice_4_tuple" {WHERE} {where_on_demand} GROUP BY {groupby_sql} fill(none)'
                    # open table
                    ondemand_panels[3]['title'] = f'Open: Client <-> Server - {metric}'
                    ondemand_panels[3]['targets'][0]['query'] = f'SELECT sum("{metric}") FROM "tcp_open_4_tuple" {WHERE} {where_on_demand} GROUP BY {groupby_sql} fill(none)'
                    for on_panel in ondemand_panels:
                        panels.append(on_panel)
                else:
                    # add ip panels 
                    if ip_m:
                        where_sql = re.sub(r'server_', '', where_sql)
                        where_sql = re.sub(r'client_', '', where_sql)
                        ip_row = copy.deepcopy(dashboard['panels'][2])
                        ip_row['id'] = next_panel_id
                        next_panel_id += 1
                        ip_row["gridPos"], next_pos_y  = update_panel_position_y(ip_row['gridPos'], next_pos_y)
                        ip_row['title'] = f'IP {where_sql[4:]}'
                        panels.append(ip_row)
                        for m_ip in ip_m:
                            sql = f'SELECT sum("{metric}") FROM "{m_ip}" {WHERE} {where_sql} {GROUPBY}, "ip" fill(none)'
                            # create panel
                            ip_panel: Dict = copy.deepcopy(template_panel)
                            ip_panel['title'] = f'{m_ip} - "{metric}" with {where_sql[4:]}'
                            ip_panel['id'] = next_panel_id
                            next_panel_id += 1
                            ip_panel["gridPos"], next_pos_y  = update_panel_position_y(ip_panel['gridPos'], next_pos_y)
                            ip_target: Dict = ip_panel['targets'][0]
                            ip_target['alias'] = "$tag_ip"
                            ip_target['query'] = sql
                            panels.append(ip_panel)
                    pass
            else:
                # add template variable
                if not self._is_ip_dashboard(measurements):
                    variable: Dict = schema['variable']
                    variable['label'] = key
                    variable['name'] = name
                    variable['query'] = f'SHOW TAG VALUES FROM "{m_name}" WITH KEY IN ({groupby_sql})'
                    dashboard['templating']['list'].append(variable)
        return dashboard
            
    def _is_ip_dashboard(self, measurements: Dict[str, Tuple[Optional[List[Tuple[str, List[str]]]], Optional[List[str]]]]) -> bool:
        for _, s in measurements.items():
            m, ip_m = s
            if not ip_m or not m:
                return False
            for measurement in m:
                m_name, _ = measurement
                if m_name not in ip_m:
                    return False
        return True


if __name__ == "__main__":
    file = "/Users/mzheng/Work/community-dashboards/dashboards/schema/database.schema.jsonc"
    db: Database = Database(file)
    creator: DashboardCreator = DashboardCreator(db)
    # creator.create(["bytes_server"], "custom application")
    # creator.create(["bytes_server"], "custom application", "Core servers")
    creator.create(["bytes_server"], "IP", "10.51.10.182")