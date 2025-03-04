from itertools import groupby

from quisby import custom_logger
from quisby.benchmarks.speccpu.graph import graph_speccpu_data
from quisby.sheet.sheet_util import (
    append_to_sheet,
    read_sheet,
    get_sheet,
    create_sheet, clear_sheet_data, clear_sheet_charts,
)
from quisby.util import combine_two_array_alternating
from quisby.util import combine_two_array_alternating, merge_lists_alternately, read_config
from quisby.benchmarks.coremark.graph import graph_coremark_data
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

def compare_speccpu_results(spreadsheets, spreadsheetId, test_name):
    spreadsheet_name = []
    values = []
    table_name = ["System name", "Price-perf"]
    results = []
    test_name = "speccpu"

    for spreadsheet in spreadsheets:
        values.append(read_sheet(spreadsheet, range=test_name))
        spreadsheet_name.append(get_sheet(spreadsheet, test_name=test_name)["properties"]["title"])

    for index, value in enumerate(values):
        values[index] = (list(g) for k, g in groupby(value, key=lambda x: x != []) if k)

    list_1 = list(values[0])
    list_2 = list(values[1])

    for value in list_1:
        for ele in list_2:
            # Check max throughput
            if value[0][0] == ele[0][0] == "System name" and value[0][1].split("-")[0] == ele[0][1].split("-")[0]:
                if compare_inst(value[1][0], ele[1][0]):
                    results.append([""])
                    for item1 in value:
                        for item2 in ele:
                            if item1[0] == item2[0]:
                                results = merge_lists_alternately(results, item1, item2)
                    break

            elif value[0][0] == "Cost/Hr" and ele[0][0] == "Cost/Hr":
                if compare_inst(value[1][0], ele[1][0]):
                    results.append([""])
                    for item1 in value:
                        for item2 in ele:
                            if item1[0] == item2[0]:
                                results.append(item1)
                    break

            elif value[0][0] == ele[0][0] == "Price-perf" and value[0][1].split("-")[0] == ele[0][1].split("-")[0]:
                if compare_inst(value[1][0], ele[1][0]):
                    results.append([""])
                    for item1 in value:
                        for item2 in ele:
                            if item1[0] == item2[0]:
                                results = merge_lists_alternately(results, item1, item2)
                    break
    try:
        create_sheet(spreadsheetId, test_name)
        custom_logger.info("Deleting existing charts and data from the sheet...")
        clear_sheet_charts(spreadsheetId, test_name)
        clear_sheet_data(spreadsheetId, test_name)
        custom_logger.info("Appending new " + test_name + " data to sheet...")
        append_to_sheet(spreadsheetId, results, test_name)
        #graph_speccpu_data(spreadsheetId, test_name, "compare")
    except Exception as exc:
        custom_logger.debug(str(exc))
        custom_logger.error("Failed to append data to sheet")
        return spreadsheetId
