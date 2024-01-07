import json
import sys

# The key of property to update value with
DATASOURCS_LIST = {"indicators", "flows", "tcp", "applications", "dns", "dhcp", "https", "icmp", "ip_map", "sys", "influxdb_health"}

def gather_datasource_mappings(file):
    with open(file, "r") as dash_json:
        dash_obj = json.load(dash_json)

    mappings = {}
    for ds in dash_obj:
        name = ds["name"]
        for item in DATASOURCS_LIST:
            if ("_"+item in name):
                if item not in mappings.keys():
                    mappings[item] = [name]
                else:
                    mappings[item].append(name)
    print(mappings)

# Press the green button in the gutter to run the script.
if __name__ == "__main__":
    gather_datasource_mappings(sys.argv[1]+"/datasource.json")
