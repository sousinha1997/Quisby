from itertools import groupby

from quisby import custom_logger
from quisby.benchmarks.fio.graph import graph_fio_run_data
from quisby.sheet.sheet_util import (
    append_to_sheet,
    read_sheet,
    get_sheet,
    create_sheet, clear_sheet_charts, clear_sheet_data
)
from quisby.util import combine_two_array_alternating


def compare_fio_run_results(spreadsheets, spreadsheetId, test_name):
    spreadsheet_name = []
    values = []
    results = []

    for spreadsheet in spreadsheets:
        values.append(read_sheet(spreadsheet, range=test_name))
        spreadsheet_name.append(get_sheet(spreadsheet, test_name)["properties"]["title"])

    for index, value in enumerate(values):
        values[index] = (list(g) for k, g in groupby(value, key=lambda x: x != []) if k)

    list_1 = list(values[0])
    list_2 = list(values[1])

    for value in list_1:
        results.append([""])
        for ele in list_2:
            if value[0] == ele[0]:
                results.append(value[0])
                results = combine_two_array_alternating(results, value[1:], ele[1:])

    try:
        create_sheet(spreadsheetId, test_name)
        custom_logger.info("Deleting existing charts and data from the sheet...")
        clear_sheet_charts(spreadsheetId, test_name)
        clear_sheet_data(spreadsheetId, test_name)
        custom_logger.info("Appending new " + test_name + " data to sheet...")
        append_to_sheet(spreadsheetId, results, test_name)
        #graph_fio_run_data(spreadsheetId, test_name, "compare")
    except Exception as exc:
        custom_logger.debug(str(exc))
        custom_logger.error("Failed to append data to sheet")
        return spreadsheetId
