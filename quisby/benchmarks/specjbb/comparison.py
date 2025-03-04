import re
from itertools import groupby

from quisby import custom_logger
from quisby.benchmarks.specjbb.graph import graph_specjbb_data
from quisby.sheet.sheet_util import (
    append_to_sheet,
    read_sheet,
    get_sheet,
    create_sheet, clear_sheet_data, clear_sheet_charts,
)
from quisby.util import combine_two_array_alternating, merge_lists_alternately, read_config


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


def compare_specjbb_results(spreadsheets, spreadsheetId, test_name, table_name=["Peak", "Peak/$eff"]):
    values = []
    results = []
    spreadsheet_name = []

    for spreadsheet in spreadsheets:
        values.append(read_sheet(spreadsheet, range=test_name))
        spreadsheet_name.append(get_sheet(spreadsheet, test_name=test_name)["properties"]["title"])

    for index, value in enumerate(values):
        values[index] = (list(g) for k, g in groupby(value, key=lambda x: x != []) if k)

    list_1 = list(values[0])
    list_2 = list(values[1])

    for value in list_1:
        for ele in list_2:
            if value[0][0] in table_name and ele[0][0] in table_name:
                if value[0][0] == ele[0][0]:
                    if compare_inst(value[1][0], ele[1][0]):
                        results.append([""])
                        header = []
                        data = []
                        for item1 in value:
                            for item2 in ele:
                                if item1[0] == item2[0]:
                                    if item1[0] in table_name:
                                        header = merge_lists_alternately(header,item1,item2)
                                        continue
                                    data = merge_lists_alternately(data, item1, item2)
                        if data:
                            results.extend(header)
                            results.extend(data)
                        break

            elif value[0][0] == "Cost/Hr" and ele[0][0] == "Cost/Hr":
                if compare_inst(value[1][0], ele[1][0]):
                    results.append([""])
                    header = []
                    data = []
                    for item1 in value:
                        for item2 in ele:
                            if item1[0] == item2[0]:
                                if item1[0] == "Cost/Hr":
                                    header.append(item1)
                                    continue
                                data.append(item1)
                    if data:
                        results.extend(header)
                        results.extend(data)
                    break
    try:
        create_sheet(spreadsheetId, test_name)
        custom_logger.info("Deleting existing charts and data from the sheet...")
        clear_sheet_charts(spreadsheetId, test_name)
        clear_sheet_data(spreadsheetId, test_name)
        custom_logger.info("Appending new " + test_name + " data to sheet...")
        append_to_sheet(spreadsheetId, results, test_name)
        #graph_specjbb_data(spreadsheetId, test_name, "compare")
    except Exception as exc:
        custom_logger.debug(str(exc))
        custom_logger.error("Failed to append data to sheet")
        return spreadsheetId


if __name__ == "__main__":
    spreadsheets = [
        "",
        "",
    ]
    test_name = "specjbb"

    compare_specjbb_results(spreadsheets, test_name, ["Peak", "Peak/$eff"])
