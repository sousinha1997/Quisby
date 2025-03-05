from itertools import groupby

from quisby import custom_logger
from quisby.sheet.sheet_util import (
    append_to_sheet,
    read_sheet,
    get_sheet,
    create_sheet, clear_sheet_charts, clear_sheet_data,
)
from quisby.util import combine_two_array_alternating,merge_lists_alternately
from quisby.util import read_config
import re


def extract_prefix_and_number(input_string):
    match = re.search(r'^(.*?)(\d+)(.*?)$', input_string)
    if match:
        prefix = match.group(1)
        suffix = match.group(3)  # Extracts the suffix after the number
        return prefix, suffix
    return None, None


def compare_inst(item1, item2):
    cloud_type = read_config("cloud", "cloud_type")
    if cloud_type == "local":
        return True
    elif cloud_type == "aws":
        return item1.split(".")[0] == item2.split(".")[0]
    elif cloud_type == "gcp":
        return item1.split("-")[0] == item2.split("-")[0]
    elif cloud_type == "azure":
        return extract_prefix_and_number(item1) == extract_prefix_and_number(item2)

def compare_uperf_results(spreadsheets, spreadsheetId, test_name):
    spreadsheet_name = []
    values = []
    results = []
    ignore_table = ["Cost/Hr"]

    for spreadsheet in spreadsheets:
        values.append(read_sheet(spreadsheet, range=test_name))
        spreadsheet_name.append(get_sheet(spreadsheet, test_name=test_name)["properties"]["title"])

    for index, value in enumerate(values):
        values[index] = (list(g) for k, g in groupby(value, key=lambda x: x != []) if k)

    list_1 = list(values[0])
    list_2 = list(values[1])

    for value in list_1:
        for ele in list_2:
            if value[0] == ele[0] and value[0][0] =="Price-Perf":
                v1 = value[1][1].split("-")[-1]
                v2 = ele[1][1].split("-")[-1]
                if value[1][1].replace(v1,"") == ele[1][1].replace(v2,""):
                    results.append([""])
                    header = [value[0]]
                    data = []
                    for item1 in value[1:]:
                        for item2 in ele[1:]:
                            if item1[0] == item2[0]:
                                if item1[0] == "Instance Count":
                                    header = merge_lists_alternately(header, item1, item2)
                                    continue
                                data = merge_lists_alternately(data, item1, item2)
                    if data:
                        results.extend(header)
                        results.extend(data)
                    break

            elif value[0] == ele[0] and (value[0][0] not in ignore_table):
                results.append([""])
                results.append(value[0])
                results = combine_two_array_alternating(results, value[1:], ele[1:])
                break

            elif value[0][0] == "Cost/Hr" and ele[0][0] == "Cost/Hr":
                if value[1][0] == ele[1][0]:
                    results.append([""])
                    for item1 in value:
                        for item2 in ele:
                            if item1[0] == item2[0]:
                                results.append(item1)
                    break

    try:
        create_sheet(spreadsheetId, test_name)
        custom_logger.info("Deleting existing charts and data from the sheet...")
        clear_sheet_charts(spreadsheetId, test_name)
        clear_sheet_data(spreadsheetId, test_name)
        custom_logger.info("Appending new " + test_name + " data to sheet...")
        append_to_sheet(spreadsheetId, results, test_name)
    except Exception as exc:
        custom_logger.debug(str(exc))
        custom_logger.error("Failed to append data to sheet")
        return spreadsheetId
