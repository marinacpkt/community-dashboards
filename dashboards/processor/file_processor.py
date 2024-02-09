from abc import ABC, abstractmethod
import json
import os
import re
import shutil
from typing import Dict, List, Optional, Set, Tuple
from dashboards.config.application_constants import KEY_CUSTOM_APPLICATION
from dashboards.editor.dashboard_editor import DashboardTransformError
from dashboards.processor.dashboard_processor import DashboardTransformConfigError, AbstractProcessor

CONVERTED_PATH_NAME = "converted"
# merged collectors
FOLDERS_WITH_MERGED_GLOBAL_DASHBOARDS = {'flow_analytics', 'tcp_analytics', 'ip_troubleshooting', 'custom'}
# per collector
FOLDERS_WITH_SEPARATE_GLOBAL_DASHBOARDS = {'application_analytics', 'debug', 'devices', 'system'}
# both
COPY_FORWARD_ORIGINAL = False
OUTPUT_FOLDER_PER_COLLECTOR = True
   
def print_error(text):
    RED = '\033[91m'
    RESET = '\033[0m'
    print(f"{RED}{text}{RESET}")

def dashboard_to_file(dashboard: Dict, output_path: str, dash_sub_path_to_file: str) -> str:
    """ Write dashboard from Dict to json file """
    output_full = f'{output_path}/{dash_sub_path_to_file}'
    path = os.path.dirname(output_full)
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
    with open(output_full, "w") as f:
        json.dump(dashboard, f, indent=2)
        f.write('\n')
    return output_full

class AbstractFileProcessor(ABC):
    
    @abstractmethod
    def process(self, processor: AbstractProcessor, key = None):
        raise NotImplementedError

    @abstractmethod
    def _write_file(self, file, folder_out, dash_converted: Optional[List[Tuple[Dict, Optional[str]]]]) -> Tuple[int, str, Optional[str], Optional[str]]:
        raise NotImplementedError


class DashboardFileProcessor(AbstractFileProcessor):

    def __init__(self, foler_or_file_in, folder_out = None):
        # for code reading only: list of internal states being maintained
        self._folder_or_file_in = None
        self._folder_in = None
        self._folder_out = None
        self._is_file = False
        self._remove_folder_before_writing = False  
        # update state values
        self._update_inputs(foler_or_file_in, folder_out)

    # for internal(testing) access only
    def _print_states(self):
        print(f'_folder_or_file_in: {self._folder_or_file_in}')
        print(f'_folder_in: {self._folder_in}')
        print(f'_folder_out: {self._folder_out}')
        print(f'_is_file: {self._is_file}')
        print(f'_remove_folder_before_writing: {self._remove_folder_before_writing}')

    # for internal access only
    def _update_inputs(self, value_foler_or_file_in, value_folder_out = None) -> None:
        # input file
        if not value_foler_or_file_in or not os.path.exists(value_foler_or_file_in):
            raise DashboardTransformConfigError(f'File/folder not specified or does not exist: {value_foler_or_file_in}')
        # is file
        self._is_file = os.path.isfile(value_foler_or_file_in)
        if self._is_file and not (os.path.basename(value_foler_or_file_in).endswith('.json') or os.path.basename(value_foler_or_file_in).endswith('.jsonc')):
            raise DashboardTransformConfigError(f'File specified is not a dashboard .json file: {value_foler_or_file_in}')
        self._folder_or_file_in = value_foler_or_file_in
        self._folder_in = os.path.dirname(self._folder_or_file_in) if self._is_file else self._folder_or_file_in
        # output folder
        self._remove_folder_before_writing = False
        if not value_folder_out:
            self._folder_out = f'{self._folder_in}/{CONVERTED_PATH_NAME}'
            self._remove_folder_before_writing = True
        elif value_folder_out == '.':
            self._folder_out = f'{self._folder_in}'
        else:
            if not value_folder_out or not os.path.exists(value_folder_out):
                raise DashboardTransformConfigError(f'File/folder not specified or does not exist: {value_folder_out}')
            self._folder_out = value_folder_out
    
    # for internal access only
    def _get_uids(self) -> Tuple[Dict[str, str], List[str], List[str]]:
        uids: Dict[str, str] = dict()
        glogal_uids: List[str] = list()
        collector_uids: List[str] = list()
        uid_set: Set[str] = set()
        for dirpath, _, filenames in os.walk(self._folder_or_file_in):
            for filename in filenames:
                if filename.endswith('.json'):
                    file = f'{dirpath}/{filename}'
                    file_uid = self._get_uid_for_file(file)
                    if file_uid:
                        if file_uid in uid_set:
                            raise DashboardTransformConfigError(f'Duplicate dashboard UID({file_uid}) for file {uids[file_uid]} and {file}. Please fix before continue.')
                        uids[file] = file_uid
                        uid_set.add(file_uid)
                        if os.path.basename(dirpath) in FOLDERS_WITH_MERGED_GLOBAL_DASHBOARDS:
                            glogal_uids.append(file_uid)
                        elif os.path.basename(dirpath) in FOLDERS_WITH_SEPARATE_GLOBAL_DASHBOARDS:
                            collector_uids.append(file_uid) 
        return uids, glogal_uids, collector_uids
    
    # for internal access only
    def _get_uid_for_file(self, file) -> Optional[str]:
        with open(file, 'r') as dash_json:
            dash_obj: Dict = json.load(dash_json)
            if isinstance(dash_obj, Dict) and 'uid' in dash_obj.keys():
                return dash_obj['uid']
        return None

    def _convert_folder(self,folder_in, folder_out, converter: AbstractProcessor, key = None, path_to_exclude = None) -> None:
        """ Convert the dashboards from folder_in and write to folder_out.
        A few use cases of different folder_out parameter:
        * Set folder_out to a completely different location: useful for sharing the whole output folder of dashboards as a complete collection.
        * Set folder_out to '.' for writing to the same folder as folder_in: useful for editing in place.
        * Empty folder_out means writting to a "converted" folder in each folder and sub folder of folder_in: useful while developing and compare the after vs before.
        """
        if path_to_exclude and path_to_exclude.strip() == folder_in.strip():
            return 
        children = os.listdir(folder_in)
        num_from = 0
        num_to = 0
        for child in children: 
            child_path = os.path.join(folder_in, child)
            if (os.path.isdir(child_path)):
                output_path = f'{folder_out}/{child}'
                self._convert_folder(child_path, output_path, converter, key, path_to_exclude)
            else:
                try:
                    if str(child).endswith(".json"):
                        num, _, _, _ = self._convert_file(f'{folder_in}/{child}', folder_out, converter, key)
                        if num > 0:
                            num_from = num_from + 1
                            num_to = num_to  + num
                            # print(f'{os.path.basename(file_ori)} converted to {num} dashboards: {files_converted}. {"Written to " if folder_written and len(folder_written) >0 else ""}{folder_written}')
                except DashboardTransformError as te:
                    print_error(f"DashboardTransformError converting file {child}: {te}")
                    continue
                except Exception as e:
                    print_error(f"Exception converting file {child}: {e}")
                    continue
        if num_to > 0:
            print(f'{num_from} converted to {num_to} dashboards to global dashboards for folder: {folder_in}.')

    def _convert_file(self, file, folder_out, converter: AbstractProcessor, key = None) -> Tuple[int, str, Optional[str], Optional[str]]:
        if not (file and len(file) > 0 and os.path.exists(file)):
            raise DashboardTransformError('The file path is an empty str. Please check the passed in file.')
        if not os.path.basename(file).endswith(".json"):
            raise DashboardTransformError(f'Only .json files are accepted. Wrong file format: {file}')
        if not os.path.exists(file.strip()): 
            raise DashboardTransformError(f'The file passed in does not exist: {file}')
        # convert
        with open(file, "r") as dash_json:
            dashboard: Dict = json.load(dash_json)
        dash_converted: Optional[List[Tuple[Dict, Optional[str]]]] = converter.process_dashboard(dashboard, key)
        # write out
        if dash_converted and len(dash_converted) > 0:
            return self._write_file(file, folder_out, dash_converted)
        return 0, file, None, None

    # request as: process(file=<file>.json, processor=AbstractDashboardGenerator)
    # processor takes in: dash, file, key
    # override
    def process(self, processor: AbstractProcessor, key = None):
        # validate inputs
        if not isinstance(processor, AbstractProcessor):
            raise DashboardTransformConfigError(f'Dashboard processors are required for this function. Expected "processosr" as instances of {AbstractProcessor.__class__.__name__}. Got: {type(processor)}')
        # process
        if self._is_file:
            num, file_ori, files_converted, folder_written =  self._convert_file(self._folder_or_file_in, self._folder_out, processor, key)
            print(f'{num} dashboards converted from template {os.path.basename(file_ori)} to: {files_converted}. Written to folder: {folder_written}')
        else:
            self._convert_folder(self._folder_or_file_in, self._folder_out, processor, key = key, path_to_exclude=self._folder_out if self._remove_folder_before_writing else None)
    
    # override
    def _write_file(self, file, folder_out, dash_converted: Optional[List[Tuple[Dict, Optional[str]]]]) -> Tuple[int, str, Optional[str], Optional[str]]:
        # write out
        if dash_converted and len(dash_converted) > 0:
            converted_filenames = ""
            folder_written = ""
            for dashboard, filename in dash_converted:      # default to return dashboard uid for filename. 
                if dashboard and filename and len(filename.strip()) > 0:
                    folder_written = dashboard_to_file(dashboard, folder_out, f'{filename}.json')
                    converted_filenames = f'{converted_filenames}{"" if len(converted_filenames) == 0 else ", "}{os.path.basename(folder_written)}'
            return (len(dash_converted), os.path.basename(file), converted_filenames, os.path.dirname(folder_written))
        return 0, file, None, None

class GlobalCollectorFileProcessor(DashboardFileProcessor):
    def __init__(self, foler_or_file_in, folder_out=None):
        super().__init__(foler_or_file_in, folder_out)
        self._file_uids: Dict[str, str] = None
        self._global_uid_list: List[str] = None
        self._collector_uid_list: List[str] = None

    # override
    def process(self, collector_config_file):
        from dashboards.processor.collector_processor.collector_processor import CollectorProcessor
        # remove the root output path if using default path (for dev testing) if exists (usually from previous run)
        if self._remove_folder_before_writing and CONVERTED_PATH_NAME in self._folder_out:
            if os.path.exists(self._folder_out):
                shutil.rmtree(self._folder_out)
        # update uids
        self._file_uids, self._global_uid_list, self._collector_uid_list = self._get_uids()
        # configs
        collector_converter = CollectorProcessor(collector_config_file, self._global_uid_list, self._collector_uid_list)
        # convert
        super().process(collector_converter)

    # override
    def _write_file(self, file, folder_out, dash_converted: Optional[List[Tuple[Dict, Optional[str]]]]) -> Tuple[int, str, Optional[str], Optional[str]]:
        # write out
        if dash_converted and len(dash_converted) > 0:
            converted_filenames = ""
            file_written = ""
            for dashboard, collector in dash_converted:
                if dashboard and collector:
                    filename = os.path.basename(file)
                    filename_copy = os.path.basename(filename).replace('.', f'_{collector}.') if file else None
                    uid_original = self._file_uids[file]
                    if uid_original in self._collector_uid_list:
                        filename_copy =  f'{collector}/{filename_copy}' if OUTPUT_FOLDER_PER_COLLECTOR else filename_copy
                    file_written = dashboard_to_file(dashboard, folder_out, filename_copy)
                    converted_filenames = f'{converted_filenames}{"" if len(converted_filenames) == 0 else ", "}{os.path.basename(file_written)}'
            return (len(dash_converted), os.path.basename(file), converted_filenames, os.path.dirname(file_written))
        return 0, file, None, None

class TemplateDashboardFileProcessor(DashboardFileProcessor):

    def __init__(self, template_file, folder_out = None, template_key = None) -> None:
        super().__init__(template_file, folder_out)
        self._template_key = template_key

    # request as: procss(file=<template_file>, key=<template_key>)
    def process(self, template_key = None, template_file = None):
        from dashboards.processor.template_processor.template_processor import TemplateProcessor
        if not template_key:
            raise DashboardTransformConfigError(f'A template dashboard key is required for {TemplateDashboardFileProcessor.__class__.name}.')
        if template_file:
            self._update_inputs(template_file, self._folder_out)
        # convert
        template_converter = TemplateProcessor()
        super().process(template_converter, self._template_key)
    
    # override
    def _write_file(self, file, folder_out, dash_converted: Optional[List[Tuple[Dict, Optional[str]]]]) -> Tuple[int, str, Optional[str], Optional[str]]:
        # write out
        if dash_converted and len(dash_converted) > 0:
            converted_filenames = ""
            file_written = ""
            for dashboard, dashboard_key in dash_converted:
                if dashboard and dashboard_key:
                    filename = os.path.basename(file)
                    index = dashboard_key.index(':')
                    name_from = dashboard_key[:index]
                    name_to = dashboard_key[index+1:]
                    filename_to = filename
                    if re.search(r'_', filename): 
                        name_to = re.sub('\s+', '_', name_to.lower())
                        name_from = re.sub('\s+', '_', name_from.lower())
                        filename_to = filename.lower().replace(name_from, name_to)
                    else:
                        filename_to = filename.replace(name_from, name_to)
                    file_written = dashboard_to_file(dashboard, folder_out, filename_to)
                    converted_filenames = f'{converted_filenames}{"" if len(converted_filenames) == 0 else ", "}{os.path.basename(file_written)}'
                        # write original file as is
            if COPY_FORWARD_ORIGINAL:
                dashboard_to_file(dashboard, folder_out, os.path.basename(file))
            return (len(dash_converted), os.path.basename(file), converted_filenames, os.path.dirname(file_written))
        return 0, file, None, None
# testing
def convert_to_global_dashboards(args: List[str]) -> None:
    folder_in = args[1]
    folder_out = None
    if len(args) > 2:
        folder_out = args[2]
    converter = GlobalCollectorFileProcessor(folder_in, folder_out)
    converter.process("/Users/mzheng/Work/community-dashboards/dashboards/config/customer_config/hsbc_collectors.jsonc")

# testing
def convert_to_application_dashboards(args: List[str]) -> None:
    template_file = args[1]
    folder_out = os.path.dirname(template_file)
    if len(args) > 2:
        if args[2] != '\.':
            folder_out = args[2]
    # NOTE: replace KEY_CUSTOM_APPLICATION according to file passed in.
    converter = TemplateDashboardFileProcessor(template_file, folder_out=folder_out, template_key = KEY_CUSTOM_APPLICATION)
    converter.process(KEY_CUSTOM_APPLICATION)

if __name__ == "__main__":
    # convert_to_global_dashboards(["", "/Users/mzheng/Workspace/grafana_publish/grafana-cclear-utility-bundle/src/assets/dashboards"])
    convert_to_application_dashboards(["", "/Users/mzheng/Work/community-dashboards/dashboards/test/application_monitored_metrics.json"])