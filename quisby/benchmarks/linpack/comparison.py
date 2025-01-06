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

def compare_linpack_results(spreadsheets, spreadsheet_id, test_name):
    """
    Compares Linpack test results from two spreadsheets and appends the comparison results
    to the specified spreadsheet.

    This function compares the GFLOPS, scaling, and price-performance data between
    two sets of test results, calculates the percentage differences, and updates the
    results on a Google Sheet.

    Args:
        spreadsheets (list): A list of spreadsheets containing the test data to compare.
        spreadsheet_id (str): The ID of the spreadsheet to append the results to.
        test_name (str): The name of the test whose results are being compared.

    Returns:
        str: The ID of the spreadsheet where the results were appended, or the same ID if the operation fails.
    """
    values = []
    results = []
    spreadsheet_names = []

    # Read the test data from both spreadsheets
    for spreadsheet in spreadsheets:
        values.append(read_sheet(spreadsheet, test_name))
        spreadsheet_names.append(
            get_sheet(spreadsheet, test_name)["properties"]["title"]
        )

    # Initialize results with headers
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
                        "Price-perf % Diff",
                    ]
                )
                break
            elif value[0] == ele[0]:
                # Calculate percentage differences for GFLOPS, scaling, and price-performance
                price_perf = [
                    float(value[2]) / float(value[4]),
                    float(ele[2]) / float(ele[4]),
                ]
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

    # Attempt to update the spreadsheet with the new comparison data
    try:
        create_sheet(spreadsheet_id, test_name)
        custom_logger.info("Deleting existing charts and data from the sheet...")
        clear_sheet_charts(spreadsheet_id, test_name)
        clear_sheet_data(spreadsheet_id, test_name)
        custom_logger.info(f"Appending new {test_name} data to sheet...")
        append_to_sheet(spreadsheet_id, results, test_name)
    except Exception as exc:
        # Log the error and return the spreadsheet ID if the operation fails
        custom_logger.debug(str(exc))
        custom_logger.error("Failed to append data to sheet")
        return spreadsheet_id
