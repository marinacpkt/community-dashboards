import json
import re
from typing import Dict

def main(file):
    # read
    with open(file, "r") as f:
        content = f.read()
        content = re.sub(r'//.*?\n|/\*.*?\*/', '', content, flags=re.S)
        schema: Dict = json.loads(content)
    # convert
    # new_schema = []
    # for key, value in schema.items():
    #     match = re.search(r'"(.*?)"', value)
    #     if match:
    #         first_word_in_quotes = match.group(1)
    #     new_schema.append({"name": key, "key": f'metric_{first_word_in_quotes}', "value":value})
    for item in schema:
        item["graph"] = True
        item["table"] = True
    # write
    output_file = file.replace(".json", ".output.json")
    with open(output_file, "w") as f:
        f.write(json.dumps(schema, indent=4))

if __name__ == "__main__":
    file = "/Users/mzheng/Work/community-dashboards/dashboards/schema/metric.monitored.json"
    main(file)