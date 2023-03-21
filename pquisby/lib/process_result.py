import logging
from sheet.sheet_util import (create_sheet, append_to_sheet, create_spreadsheet, delete_sheet_content)
from benchmarks.uperf.uperf import create_summary_uperf_data
from benchmarks.uperf.graph import graph_uperf_data
from benchmarks.uperf.comparison import compare_uperf_results


def process_results(results, test_name, run_name, spreadsheet_name, spreadsheetId):
    # Create spreadsheet if it doesn't exist, otherwise delete old records
    if not spreadsheetId:
        spreadsheetId = create_spreadsheet(spreadsheet_name, test_name)
    else:
        delete_sheet_content(spreadsheetId, test_name)

    # Summarise data
    try:
        results = globals()[f"create_summary_{test_name}_data"](results, run_name, "9")
    except Exception as exc:
        logging.error("Error summarising " + str(test_name) + " data")
        print(str(exc))
        return

    # Create sheet and add data
    try:
        create_sheet(spreadsheetId, test_name)
        append_to_sheet(spreadsheetId, results, test_name)
    except Exception as exc:
        logging.error("Error appending " + str(test_name) + " data to sheet")
        return

    # Graphing up data
    try:
        globals()[f"graph_{test_name}_data"](spreadsheetId, test_name)
    except Exception as exc:
        logging.error("Error graphing " + str(test_name) + " data")
        return
    return spreadsheetId
