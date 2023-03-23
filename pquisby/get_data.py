import configparser
import json
import logging
import os.path
import requests
from benchmarks.uperf.uperf import extract_uperf_data
from process_result import process_results
from sheet.sheet_util import delete_spreadsheet

payload = ""
headers = {'Authorization': '' }
pbench_server_url = "http://dhcp-214.ctrl.perf-infra.lab.eng.rdu2.redhat.com:8080"

def get_benchmark_details(resourceid, run_name,custom_headers):
    url = f"{pbench_server_url}/api/v1/datasets/inventory/{resourceid}/metadata.log"
    print(url)
    response = requests.get(url, headers=custom_headers, data=payload,stream=True)
    decoded_response = response.content.decode("UTF-8")
    parser = configparser.ConfigParser(allow_no_value=True)
    parser.read_string(decoded_response)
    benchmark_name = parser.get("pbench", "script")
    controller_name = parser.get("run", "controller")
    return benchmark_name, controller_name


def register_details_json(test_name, spreadsheet_id):
    filename = os.path.join(os.environ['quisby_conf_dir'],"charts.json")
    if not os.path.exists(filename):
        data = {"chartlist": {test_name: spreadsheet_id}}
        with open(filename, "w") as f:
            json.dump(data, f)
    else:
        with open(filename, "r") as f:
            data = json.load(f)
        data["chartlist"][test_name] = spreadsheet_id
        with open(filename, "w") as f:
            json.dump(data, f)

def delete_entry_from_json(run_name):
    filename = os.path.join(os.environ['quisby_conf_dir'],"charts.json")
    with open(filename, "r") as f:
        data = json.load(f)
    del data["chartlist"][run_name]
    with open(filename, "w") as f:
        json.dump(data, f)


def check_if_chart_exists(test_name):
    filename = os.path.join(os.environ['quisby_conf_dir'],"charts.json")
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


def fetch_test_data(resourceid, run_name,custom_headers):
    results = []
    benchmark_name, controller_name = get_benchmark_details(resourceid, run_name, custom_headers)

    spreadsheet_name = run_name
    url = f"{pbench_server_url}/api/v1/datasets/inventory/{resourceid}/result.csv"
    response = requests.get(url, headers=custom_headers, data=payload,stream=True)
    decoded_data = response.content.decode("UTF-8")
    split_rows = decoded_data.split("\n")
    csv_data = []
    for row in split_rows:
        csv_data.append(row.split(","))
    if benchmark_name == "uperf":
        test_name = "uperf"
        ret_val,json_data = extract_uperf_data(controller_name, csv_data,run_name)
        if ret_val:
            results += ret_val
        else:
            logging.ERROR("No data to chart")
            return None, None, None
    spreadsheet_id = check_if_chart_exists(run_name)
    if spreadsheet_id == "":
        spreadsheet_id = process_results(results, test_name,run_name, spreadsheet_name, spreadsheet_id)
        register_details_json(run_name, spreadsheet_id)
    else:
        spreadsheet_id = process_results(results, test_name,run_name, spreadsheet_name, spreadsheet_id)
    return spreadsheet_id, json_data, benchmark_name



def delete_test_data(resourceid,run_name):
    spreadsheet_id = check_if_chart_exists(run_name)
    if spreadsheet_id == "":
        print("Sheet doesn't exist")
    else:
        delete_entry_from_json(run_name)
    delete_spreadsheet(spreadsheet_id)
    return spreadsheet_id

# delete_test_data("e8b03087a03c5986b47b58f6ad84a907","uperf__2023.03.01T05.17.05")
