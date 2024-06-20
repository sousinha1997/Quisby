from quisby import custom_logger
from itertools import groupby

from quisby.sheet.sheet_util import (
    create_spreadsheet,
    append_to_sheet,
    read_sheet,
    get_sheet,
    create_sheet, clear_sheet_data, clear_sheet_charts,
)
from quisby.util import combine_two_array_alternating, merge_lists_alternately
from quisby.benchmarks.coremark.graph import graph_coremark_data


def compare_coremark_results(spreadsheets, spreadsheetId, test_name, table_name=["System name"]):
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
            # Check max throughput
            if value[0][0] in table_name and ele[0][0] in table_name:
                results.append([""])
                for item1 in value:
                    for item2 in ele:
                        if item1[0] == item2[0]:
                            results = merge_lists_alternately(results, item1, item2)
                break

            elif value[1][0] == ele[1][0]:
                if value[0][0] == ele[0][0]:
                    results.append([""])
                    results.append(value[0])
                    for item1, item2 in zip(value[1:], ele[1:]):
                        results = merge_lists_alternately(results, item1, item2)
                    break

    try:
        create_sheet(spreadsheetId, test_name)
        custom_logger.info("Deleting existing charts and data from the sheet...")
        clear_sheet_charts(spreadsheetId, test_name)
        clear_sheet_data(spreadsheetId, test_name)
        custom_logger.info("Appending new " + test_name + " data to sheet...")
        append_to_sheet(spreadsheetId, results, test_name)
        # graph_coremark_data(spreadsheetId, test_name)
    except Exception as exc:
        custom_logger.debug(str(exc))
        custom_logger.error("Failed to append data to sheet")
        return spreadsheetId




if __name__ == "__main__":
    spreadsheets = [
        "1MsO506DIQOt_fcDqwJr3mFOqi_77fQxnWvj6k4qFpZk",
        "1Z9YUCM22mD2mJ_NeudaMJmdeQhUHsshmGb-3XQRVd5Y",
    ]
    test_name = "coremark"

    compare_coremark_results(spreadsheets,"1x-XjP0S74D-dbsBMmHufLHhjsiK994h29QcOUxNwdcE", test_name,
                            table_name=["System Name"])
