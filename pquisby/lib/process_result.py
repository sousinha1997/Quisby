import logging
from pquisby.lib.sheet.sheet_util import (create_sheet, append_to_sheet, create_spreadsheet, delete_sheet_content)
from pquisby.lib.benchmarks.uperf.uperf import create_summary_uperf_data
from pquisby.lib.benchmarks.uperf.graph import graph_uperf_data
from pquisby.lib.benchmarks.uperf.comparison import compare_uperf_results



def process_results(results, test_name, os_version, spreadsheet_name, spreadsheet_id):
    # Create spreadsheet if it doesn't exist, otherwise delete old records
    if not spreadsheet_id:
        spreadsheet_id = create_spreadsheet(spreadsheet_name, test_name)
    else:
        delete_sheet_content(spreadsheet_id, test_name)

    # Summarise data
    try:
        results = globals()[f"create_summary_{test_name}_data"](results, spreadsheet_name, os_version)
    except Exception as exc:
        logging.error("Error summarising " + str(test_name) + " data")
        print(str(exc))
        return

    # Create sheet and add data
    try:
        create_sheet(spreadsheet_id, test_name)
        append_to_sheet(spreadsheet_id, results, test_name)
    except Exception as exc:
        logging.error("Error appending " + str(test_name) + " data to sheet")
        return

    # Graphing up data
    try:
        globals()[f"graph_{test_name}_data"](spreadsheet_id, test_name)
    except Exception as exc:
        logging.error("Error graphing " + str(test_name) + " data")
        return
    return spreadsheet_id
