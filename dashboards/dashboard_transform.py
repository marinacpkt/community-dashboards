import json
import os
import shutil
import sys
from typing import Dict, List, Optional, Tuple
from dashboards.shared.constants import KEY_CUSTOM_APPLICATION
from dashboards.shared.commons import AbstractDashboardEditor, DashboardTransformError

CONVERTED_PATH_NAME = "converted"
""""
 TODO:
Redesign to:
* enable converting separate and merge in one call?
* enable pass in a pipeline of methods to apply? (pass in dashboard Dict, return dashboard Dict)
* add an api to create datasources per collector if not already existing
* build API out of it for pass in a dashboard json and apply specified transformations
  - converting from single collector to multiple (separate or merged)
  - converting dashboard to similar schema dashboard: e.g. hosts group to custom application.
  - apply a pipeline of transformations e.g. graph, table, string replace.
""" 


def print_error(text):
    RED = '\033[91m'
    RESET = '\033[0m'
    print(f"{RED}{text}{RESET}")


def convert_folder(folder_in: str, folder_out: str, converters: List[AbstractDashboardEditor]) -> None:
    """ Convert the dashboards from folder_in and write to folder_out.
    A few use cases of different folder_out parameter:
    * Set folder_out to a completely different location: useful for sharing the whole output folder of dashboards as a complete collection.
    * Set folder_out to '.' for writing to the same folder as folder_in: useful for editing in place.
    * Empty folder_out means writting to a "converted" folder in each folder and sub folder of folder_in: useful while developing and compare the after vs before.
    """
    children = os.listdir(folder_in)
    key_converter = 'converter'
    key_file_count = 'file_count'
    file_processed: Dict = {key_converter: None, key_file_count: 0}
    for child in children: 
        child_path = os.path.join(folder_in, child)
        if (os.path.isdir(child_path)):
            output_path = f'{folder_out}/{child}'
            convert_folder(child_path, output_path, converters)
        else:
            try:
                if str(child).endswith(".json"):
                    for converter in converters:
                        dash_converted = converter.from_file(f'{folder_in}/{child}')
                        if dash_converted and len(dash_converted) > 0:
                            for dash in dash_converted:
                                dash_obj = dash[0]
                                dash_sub_path_to_file = dash[1]
                                if dash_obj and dash_sub_path_to_file and len(dash_sub_path_to_file) > 0:
                                    dashboard_to_file(dash_obj, folder_out, dash_sub_path_to_file)
                            file_processed[key_converter] = converter.__class__.__name__
                            file_processed[key_file_count] = file_processed[key_file_count] + 1
            except DashboardTransformError as te:
                print_error(f"DashboardTransformError converting file {child}: {te}")
                continue
            # except Exception as e:
            #     print_error(f"Exception converting file {child}: {e}")
            #     continue
    if file_processed[key_file_count] > 0:
        print(f'{"Merged Collector" if "merged" in file_processed[key_converter].lower() else "Separate Collector"}: {file_processed[key_file_count]} dashboards converted to global dashboards for folder: {folder_in}.')


def dashboard_to_file(dash_obj: Dict, output_path: str, dash_sub_path_to_file: str) -> None:
    """ Write dashboard from Dict to json file """
    output_full = f'{output_path}/{dash_sub_path_to_file}'
    path = os.path.dirname(output_full)
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
    with open(output_full, "w") as f:
        json.dump(dash_obj, f, indent=2)
        # print(f'Write to file {output_full}')


def collector_to_global(folder_in: str, folder_out: str) -> None:
    from dashboards.convert.collectorconverter.per_collector_converter import GlobalPerCollectorConverter
    from dashboards.convert.collectorconverter.merged_collectors_converter import GlobalMergedCollectorConverter
    # global dashboard per collector
    per_collector_converter = GlobalPerCollectorConverter()
    mergeg_collector_converter = GlobalMergedCollectorConverter()
    # convert_folder(folder_in, folder_out, [per_collector_converter])
    # convert_folder(folder_in, folder_out, [mergeg_collector_converter])
    convert_folder(folder_in, folder_out, [per_collector_converter, mergeg_collector_converter])


def transform(folder_in: str, folder_out: str) -> None:
    """ TODO: apply a pipeline of transformations to a folder of dashboards. This would help update dashboard elements where 
    text search and replace is applied otherwise."""
    pass


def application_from_template(file_application: str, folder_out: str) -> None:
    """ TODO: generate other application dashboards from a template dashboard
    Applications inlude: hosts_group, custom_application, tls_domain, cname_domain
     """
    from dashboards.convert.application_converter import ApplicationConverter
    dash_converted: Optional[List[Tuple[Dict, Optional[str]]]] = ApplicationConverter.from_file(file_application, KEY_CUSTOM_APPLICATION)
    file_processed = 0
    if dash_converted and len(dash_converted) > 0:
        filenames = list()
        for dash in dash_converted:
            dash_obj = dash[0]
            dash_sub_path_to_file = dash[1]
            if dash_obj and dash_sub_path_to_file and len(dash_sub_path_to_file) > 0:
                dashboard_to_file(dash_obj, folder_out, dash_sub_path_to_file)
                filenames.append(dash_sub_path_to_file)
                file_processed = file_processed + 1
    if file_processed > 0:
        print(f'{file_processed} dashboards written to folder: {folder_out}.\nConverted from template {os.path.basename(file_application)} to: {", ".join(filenames)}')


def ips_for_an_application_from_template(file_ips_for_an_application: str, folder_in: str, folder_out: str) -> None:
    """ TODO: generate other level 2 dashboards from a template level 2 dashboard
    Applications inlude: vlan, application port, and any other ip tags e.g. hosts_group, custom_application, 
     """
    pass

def convert_to_global_dashboards(args: List[str]) -> None:
    folder_in = args[1]
    folder_out = None
    if len(args) > 2:
        if args[2] == '\.':
            folder_out = args[1]
        else:
            folder_out = args[2]
    # remove the root output path if using default path (for dev testing) if exists (usually from previous run)
    if folder_out is None:
        folder_out = folder_in+"/"+CONVERTED_PATH_NAME
        if os.path.exists(folder_out):
            shutil.rmtree(folder_out)
    collector_to_global(folder_in, folder_out)

def conver_to_application_dashboards(args: List[str]) -> None:
    template_file = args[1]
    folder_out = os.path.dirname(template_file)
    if len(args) > 2:
        if args[2] != '\.':
            folder_out = args[2]
    application_from_template(template_file,folder_out)

# Press the green button in the gutter to run the script.
def main():
    """ Convert the input folder of dashboard and write to either the provided output path or a default (/converted) path in the input folder.
    If provided output path is the same as the input path, it overwrites the input files: edit in place. 
    Parameters:
    sys.argv[1]: the path to the input folder with dashboards to convert.
    sys.argv[2]: the path to write the converted files to.
    """
    convert_to_global_dashboards(sys.argv)
    # conver_to_application_dashboards(sys.argv)

if __name__ == "__main__":
    main()