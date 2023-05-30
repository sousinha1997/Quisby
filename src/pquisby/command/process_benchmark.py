import logging
import os
import shutil
import click
from pquisby.lib.process_result import data_handler, extract_data
from pquisby.lib.util import write_config


@click.command()
@click.option('-l', '--results', help="Results (results_path")
@click.option('-t', '--test-name', help="Benchmark test name")
@click.option('-v', '--os-type', help="Distro")
@click.option('-v', '--os-version', help="Distro version")
@click.option('-s', '--system-name', help="Controller Name")
@click.option('-d', '--dataset-name', help="Dataset Name")
@click.option('-n', '--spreadsheet-name', help="Any specific spreadsheet name")
@click.option('-i', '--spreadsheet-id', help="Any specific spreadsheet")
@click.option('-v', '--cloud', help="cloud/local")
@click.option('-p', '--platform', help="platform for processing")
@click.option('-c', '--config-path', help="config-path")
@click.option('-it', '--input_type', help="data type for processioning , file/csv/stream ")
def process_run(results, test_name, os_type, os_version, system_name, dataset_name, spreadsheet_name, spreadsheet_id, cloud, platform,
                config, input_type):
    if config:
        config_location = config
    else:
        logging.INFO("No config path found,switching to default location")
        conf_dir = os.getenv("HOME") + "/.config/pquisby/"
        config_location = conf_dir + "config.ini"
        if os.path.exists(config_location):
            pass
        else:
            logging.error("Unable to find config at default location, creating...")
            # Copy the file to the destination directory
            shutil.copy("pquisby/lib/sample_files/config.ini", conf_dir)
            return
    if results:
        write_config(config_location, "test", "results", results)
    if test_name:
        write_config(config_location, "test", "test_name", test_name)
    if os_type:
        write_config(config_location, "test", "os_type", os_type)
    if os_version:
        write_config(config_location, "test", "os_version", os_version)
    if system_name:
        write_config(config_location, "test", "system_name", system_name)
    else:
        system_name = "baremetal"
        write_config(config_location, "test", "system_name", system_name)
    if dataset_name:
        write_config(config_location, "test", "dataset_name", dataset_name)
    else:
        dataset_name = "test_" +test_name+"_"+system_name+"_"+os_type+"_"+os_version
        write_config(config_location, "test", "dataset_name", dataset_name)
    if input_type:
        write_config(config_location, "test", "input_type", input_type)
    else:
        input_type = "file"
        write_config(config_location, "test", "input_type", input_type)
    if spreadsheet_name:
        write_config(config_location, "spreadsheet", "spreadsheet_name", spreadsheet_name)
    if spreadsheet_id:
        write_config(config_location, "spreadsheet", "spreadsheet_id", spreadsheet_id)
    if cloud:
        write_config(config_location, "cloud", "cloud_type", cloud)
    else:
        write_config(config_location, "cloud", "cloud_type", "baremetal")

    if platform == "pbench":
        json_res = extract_data(test_name, dataset_name, system_name, input_type, results)
        if json_res["jsonData"]:
            return json_res["jsonData"]

    elif platform == "google-doc":
        spreadsheet_id = data_handler(config_location)










