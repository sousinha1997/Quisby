from itertools import groupby

from pquisby.lib.sheet.sheet_util import (
    create_spreadsheet,
    append_to_sheet,
    read_sheet,
    get_sheet,
    create_sheet
)
from pquisby.lib.util import combine_two_array_alternating
from pquisby.lib.benchmarks.fio.graph import graph_fio_run_data


def compare_fio_run_results(spreadsheets, spreadsheetId, test_name="fio_run"):
    spreadsheet_name = []
    values = []
    results = []

    for spreadsheet in spreadsheets:
        values.append(read_sheet(spreadsheet, range=test_name))
        spreadsheet_name.append(get_sheet(spreadsheet,test_name, range="!a:z")["properties"]["title"])

    for index, value in enumerate(values):
        values[index] = (list(g) for k, g in groupby(value, key=lambda x: x != []) if k)

    list_1 = list(values[0])
    list_2 = list(values[1])

    for value in list_1:
        results.append([""])
        for ele in list_2:
            if value[0][1] == ele[0][1] and value[0][2] == ele[0][2]:
                results.append(value[0])
                results = combine_two_array_alternating(results, value[1:], ele[1:])

    create_sheet(spreadsheetId, test_name)
    append_to_sheet(spreadsheetId, results, test_name)
    graph_fio_run_data(spreadsheetId, test_name)

