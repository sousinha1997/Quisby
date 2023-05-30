import json
import logging
import time

from pquisby.lib.process_result import extract_data
from pquisby.lib.sheet.sheet_util import get_sheet, create_spreadsheet
from pquisby.lib.benchmarks.uperf.comparison import compare_uperf_results


def compare_results(spreadsheet_list,test_name):

    sheet_list = []
    spreadsheet_name = []
    spreadsheets = spreadsheet_list
    # check if list is passed else convert to list
    if not isinstance(spreadsheets,list):
        spreadsheets = spreadsheets.split(",")

    for spreadsheet in spreadsheets:
        sheet_names = []
        sheets = get_sheet(spreadsheet, test_name=test_name)
        spreadsheet_name.append(get_sheet(spreadsheet, test_name=[])["properties"]["title"].strip())
        for sheet in sheets.get("sheets"):
            sheet_names.append(sheet["properties"]["title"].strip())
        sheet_list.append(sheet_names)

    if test_name:
        comparison_list = [test_name]
    else:
        # Find sheets that are present in all spreadsheets i.e intersection
        comparison_list = set(sheet_list[0])
        for sheets in sheet_list[1:]:
            comparison_list.intersection_update(sheets)
        comparison_list = list(comparison_list)

    spreadsheet_name = " and ".join(spreadsheet_name)

    comp_spreadsheetId = create_spreadsheet(spreadsheet_name, comparison_list[0])

    for index, test_name in enumerate(comparison_list):
        compare_uperf_results(spreadsheets, comp_spreadsheetId, test_name)
        if index + 1 != len(comparison_list):
            logging.info("# Sleeping 10 sec to workaround the Google Sheet per minute API limit")
            time.sleep(10)
    return spreadsheet_name,comp_spreadsheetId


def compare_csv_to_json(benchmark_name, input_type, data_stream):
    result_json = {}
    flag = 0
    for dataset_name, data in data_stream.items():
        json_res = extract_data(benchmark_name, dataset_name, "baremetal", input_type, data)
        if json_res["jsonData"]:
            json_data = json_res["jsonData"]
        if flag == 0:
            result_json = json_data
            flag = flag + 1
        else:
            for i in result_json["data"]:
                metric_unit = i["metrics_unit"]
                test_name = i["test_name"]
                for j in json_data["data"]:
                    if metric_unit == j["metrics_unit"] and test_name == j["test_name"]:
                        i["instances"].extend(j["instances"])
    return result_json

