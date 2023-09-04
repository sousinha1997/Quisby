import fileinput
import json
import logging
import os.path
from pquisby.lib.util import read_config
from pquisby.lib.sheet.sheet_util import (create_sheet, append_to_sheet, create_spreadsheet, delete_sheet_content)
from pquisby.lib.benchmarks.uperf.uperf import create_summary_uperf_data
from pquisby.lib.benchmarks.uperf.graph import graph_uperf_data
from pquisby.lib.benchmarks.uperf.comparison import compare_uperf_results
from pquisby.lib.post_processing import QuisbyProcessing


def process_results(results, test_name, cloud, os_type, os_version, spreadsheet_name, spreadsheet_id):
    # Create spreadsheet if it doesn't exist, otherwise delete old records
    if not spreadsheet_name:
        spreadsheet_name = test_name + "-" + cloud + "-" + os_type + "-" + os_version
    if not spreadsheet_id:
        spreadsheet_id = create_spreadsheet(spreadsheet_name, test_name)
    else:
        delete_sheet_content(spreadsheet_id, test_name)

    # Summarise data
    try:
        results = globals()[f"create_summary_{test_name}_data"](results, spreadsheet_name, os_version)
    except Exception as exc:
        logging.error("Error summarising " + str(test_name) + " data")
        print(str(exc))
        return

    # Create sheet and add data
    try:
        create_sheet(spreadsheet_id, test_name)
        append_to_sheet(spreadsheet_id, results, test_name)
    except Exception as exc:
        logging.error("Error appending " + str(test_name) + " data to sheet")
        return

    # Graphing up data
    try:
        globals()[f"graph_{test_name}_data"](spreadsheet_id, test_name)
    except Exception as exc:
        logging.error("Error graphing " + str(test_name) + " data")
        return
    return spreadsheet_name, spreadsheet_id


def register_details_json(spreadsheet_name, spreadsheet_id):
    home_dir = os.getenv("HOME")
    filename = home_dir + "/pquisby/charts.json"
    if not os.path.exists(filename):
        data = {"chartlist": {spreadsheet_name: spreadsheet_id}}
        with open(filename, "w") as f:
            json.dump(data, f)
    else:
        with open(filename, "r") as f:
            data = json.load(f)
        data["chartlist"][spreadsheet_name] = spreadsheet_id
        with open(filename, "w") as f:
            json.dump(data, f)


def check_if_chart_exists(test_name):
    home_dir = os.getenv("HOME")
    filename = os.path.join(home_dir, "/pquisby/charts.json")
    if not os.path.exists(filename):
        return ""
    else:
        with open(filename, "r") as f:
            data = json.load(f)
        try:
            id = data["chartlist"][test_name]
        except KeyError:
            return ""
        return id


def data_handler(config_location):
    global test_name
    global source
    global count
    results = []
    print(config_location)
    environment = read_config(config_location, 'test', 'environment')
    os_type = read_config(config_location, 'test', 'os_type')
    os_version = read_config(config_location, 'test', 'os_version')
    spreadsheet_name = read_config(config_location, 'spreadsheet', 'spreadsheet_name')
    spreadsheet_id = read_config(config_location, 'spreadsheet', 'spreadsheet_id')
    results_path = read_config(config_location, 'test', 'results')
    input_type = read_config(config_location, 'test', 'input_type')
    dataset_name = read_config(config_location, 'test', 'dataset_name')
    test_path = results_path.strip(results_path.split("/")[-1])

    if not spreadsheet_id:
        spreadsheet_id = ""

    for line in fileinput.FileInput(results_path, inplace=1):
        if line.rstrip():
            print(line, end="")

    with open(results_path) as file:
        test_result_path = file.readlines()

        for data in test_result_path:
            if "test " in data:
                if results:
                    spreadsheet_name, spreadsheet_id = process_results(results, test_name, cloud, os_type, os_version,
                                                                       spreadsheet_name,
                                                                       spreadsheet_id)
                results = []
                test_name = data.replace("test ", "").replace("results_", "").replace(".csv", "").strip()
                source = data.split()[-1].split("_")[0].strip()
            else:
                try:
                    if test_name == "fio_run":
                        data = data.strip("\n").strip("'").strip()
                        path, system_name = (data.split(",")[0] + "," + data.split(",")[1]), data.split(",")[-1]
                        path = path.replace(os.path.basename(path), "")
                    else:
                        data = data.strip("\n").strip("'")
                        path, system_name = data.split(",")
                    csv_path = test_path + "/" + path.strip()
                    json_res = QuisbyProcessing.extract_data(test_name,dataset_name, system_name, input_type, csv_path)
                    if json_res["csvData"]:
                        results += json_res["csvData"]
                except ValueError as exc:
                    logging.error(str(exc))
                    continue
        try:
            spreadsheet_name, spreadsheet_id = process_results(results, test_name, cloud, os_type, os_version,spreadsheet_name,spreadsheet_id)
        except Exception as exc:
            exception_type = type(exc)
            return {"status": "failed", "Exception": str(exc), "Exception_type": exception_type}
        print(f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
        register_details_json(spreadsheet_name, spreadsheet_id)
        return spreadsheet_id



# if __name__ == '__main__':
#    extract_data("uperf","localhost",[['iteration_number', 'iteration_name', 'Gb_sec:client_hostname:127.0.0.1-server_hostname:192.168.122.142-server_port:20010', 'Gb_sec:client_hostname:all-server_hostname:all-server_port:all', 'trans_sec:client_hostname:127.0.0.1-server_hostname:192.168.122.142-server_port:20010', 'trans_sec:client_hostname:all-server_hostname:all-server_port:all', 'usec:client_hostname:127.0.0.1-server_hostname:192.168.122.142-server_port:20010', 'usec:client_hostname:all-server_hostname:all-server_port:all'], ['1', 'tcp_stream-65535B-1i', ' 0.0010', ' 0.0010', '', '', '', '', ''], ['2', 'tcp_maerts-65535B-1i', ' 1.1396', ' 1.1396', '', '', '', '', ''], ['3', 'tcp_bidirec-65535B-1i', ' 0.8890', ' 0.8890', '', '', '', '', ''], ['4', 'tcp_rr-65535B-1i', '', '', ' 1.8146', ' 1.8146', ' 592316.6667', ' 592316.6667', ''], ['5', 'udp_stream-65535B-1i', '', '', '', '', '', '', ''], ['6', 'udp_maerts-65535B-1i', '', '', '', '', '', '', ''], ['7', 'udp_bidirec-65535B-1i', '', '', '', '', '', '', ''], ['8', 'udp_rr-65535B-1i', '', '', '', '', '', '', ''], []])
