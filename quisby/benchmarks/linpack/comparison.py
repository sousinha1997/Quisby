from quisby import custom_logger

from quisby.sheet.sheet_util import (
    read_sheet,
    append_to_sheet,
    clear_sheet_charts,
    clear_sheet_data,
    get_sheet,
    create_sheet,
)
from quisby.util import percentage_deviation


def compare_linpack_results(spreadsheets, spreadsheetId, test_name):
    values = []
    results = []
    spreadsheet_name = []

    for spreadsheet in spreadsheets:
        values.append(read_sheet(spreadsheet, test_name))
        spreadsheet_name.append(
            get_sheet(spreadsheet, test_name)["properties"]["title"]
        )

    for value in values[0]:
        for ele in values[1]:
            if value[0] == "System" and ele[0] == "System":
                results.append(
                    [
                        value[0],
                        value[1],
                        value[2],
                        ele[2],
                        "% Gflops Diff",
                        value[3],
                        ele[3],
                        "% Scaling Diff",
                        value[4],
                        value[5],
                        ele[5],
                        "Price/Perf % Diff",
                    ]
                )
                break
            else:
                if value[0] == ele[0]:
                    price_perf = []
                    price_perf.append(float(value[2]) / float(value[4]))
                    price_perf.append(float(ele[2]) / float(ele[4]))
                    price_perf_diff = percentage_deviation(price_perf[0], price_perf[1])
                    percentage_diff = percentage_deviation(value[2], ele[2])
                    gflop_diff = percentage_deviation(value[3], ele[3])
                    results.append(
                        [
                            value[0],
                            value[1],
                            value[2],
                            ele[2],
                            percentage_diff,
                            value[3],
                            ele[3],
                            gflop_diff,
                            value[4],
                            price_perf[0],
                            price_perf[1],
                            price_perf_diff,
                        ]
                    )
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
