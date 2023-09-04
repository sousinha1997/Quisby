import logging
import os
import shutil
import click
from pquisby.lib.process_result import data_handler
from pquisby.lib.post_processing import QuisbyProcessing
from pquisby.lib.util import write_config


@click.command()
@click.option('-l', '--results', help="Results")
@click.option('-t', '--test-name', help="Test name")
@click.option('-o', '--os-type', help="Distro")
@click.option('-v', '--os-version', help="Distro version")
@click.option('-d', '--dataset-name', help="Dataset Name")
@click.option('-n', '--spreadsheet-name', help="Any specific spreadsheet name")
@click.option('-i', '--spreadsheet-id', help="Any specific spreadsheet")
@click.option('-e', '--environment', help="cloud/localhost")
@click.option('-p', '--platform', help="platform for processing")
@click.option('-c', '--config-path', help="config-path")
@click.option('-it', '--input_type', help="data type for processioning , file/csv/stream ")
def process_run(results, test_name, os_type, os_version, dataset_name, spreadsheet_name, spreadsheet_id, environment, platform,
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
    else:
        return "Test name not provided"
    if os_type:
        write_config(config_location, "test", "os_type", os_type)
    else:
        return "OS type not provided"
    if os_version:
        write_config(config_location, "test", "os_version", os_version)
    else:
        return "OS version not provided"
    if environment:
        write_config(config_location, "test", "environment", system_name)
    else:
        print("Environment not provided. Taking default values..")
        environment = "baremetal"
        write_config(config_location, "test", "environment", environment)
    if dataset_name:
        write_config(config_location, "test", "dataset_name", dataset_name)
    else:
        dataset_name = "test_" +test_name+"_"+environment+"_"+os_type+"_"+os_version
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

    if platform == "pbench":
        input_type = "stream"
        json_res = QuisbyProcessing.extract_data(test_name, dataset_name, environment, input_type, results)
        if json_res["jsonData"]:
            return json_res["jsonData"]

    elif platform == "google-doc":
        spreadsheet_id = data_handler(config_location)










