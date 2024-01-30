from quisby import custom_logger
from itertools import groupby

from quisby.sheet.sheet_util import (
    append_to_sheet,
    read_sheet,
    get_sheet,
    create_sheet, clear_sheet_charts, clear_sheet_data
)
import re
from quisby.util import combine_two_array_alternating,read_config
from quisby.benchmarks.hammerdb.graph import graph_hammerdb_data

def are_in_same_group(str1, str2):
    # Extract mid values between underscores using regular expression
    pattern = re.compile(r'_(.*?)_')
    match1 = pattern.search(str1)
    match2 = pattern.search(str2)

    if match1 and match2:
        mid_value1 = match1.group(1)
        mid_value2 = match2.group(1)

        # Compare mid values ignoring numbers
        mid_value1_letters = ''.join([char for char in mid_value1 if not char.isdigit()])
        mid_value2_letters = ''.join([char for char in mid_value2 if not char.isdigit()])

        return mid_value1_letters == mid_value2_letters

    return False

def comparegroup(instances):
    cloud = read_config("cloud","cloud_type")
    if cloud == "azure":
        for i in range(0,2):
            parts = instances[i].rsplit('_', 1)
            instances[i] = parts[0]+"_"
        return are_in_same_group(instances[0], instances[1])


def compare_hammerdb_results(spreadsheets, spreadsheetId, test_name):
    spreadsheet_name = []
    values = []
    results = []

    for spreadsheet in spreadsheets:
        values.append(read_sheet(spreadsheet, range=test_name))
        spreadsheet_name.append(
            get_sheet(spreadsheet,test_name=test_name)["properties"]["title"]
        )

    for index, value in enumerate(values):
        values[index] = (list(g) for k, g in groupby(value, key=lambda x: x != []) if k)
    list_1 = sorted(list(values[0]))
    list_2 = sorted(list(values[1]))

    for value in list_1:
        results.append([""])
        for ele in list_2:
            if(comparegroup([value[0][1], ele[0][1]])):
                results = combine_two_array_alternating(results, value, ele)

    try:
        create_sheet(spreadsheetId, test_name)
        custom_logger.info("Deleting existing charts and data from the sheet...")
        clear_sheet_charts(spreadsheetId, test_name)
        clear_sheet_data(spreadsheetId, test_name)
        custom_logger.info("Appending new " + test_name + " data to sheet...")
        append_to_sheet(spreadsheetId, results, test_name)
        graph_hammerdb_data(spreadsheetId, test_name)
    except Exception as exc:
        custom_logger.error("Failed to append data to sheet")
        return spreadsheetId

