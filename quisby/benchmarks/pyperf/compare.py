import re
from itertools import groupby
from quisby import custom_logger
from quisby.sheet.sheet_util import (
    append_to_sheet,
    read_sheet,
    get_sheet,
    create_sheet,
    clear_sheet_data,
    clear_sheet_charts,
)
from quisby.util import merge_lists_alternately, read_config


# Helper function to extract prefix and suffix from instance names
def extract_prefix_and_number(input_string):
    """
    Extract the prefix and suffix from an instance name that contains a number.
    Example: "t2.micro-01" => ("t2.micro", "01")

    Args:
        input_string (str): Instance name, e.g., "t2.micro-01"

    Returns:
        tuple: (prefix, suffix) or (None, None) if no match
    """
    match = re.search(r'^(.*?)(\d+)(.*?)$', input_string)
    if match:
        prefix = match.group(1)
        suffix = match.group(3)
        return prefix, suffix
    return None, None


# Compare two instance types based on cloud configuration
def compare_inst(item1, item2):
    """
    Compares two instances based on their cloud type.

    Args:
        item1 (str): Instance type from the first sheet
        item2 (str): Instance type from the second sheet

    Returns:
        bool: True if instances match based on cloud type, False otherwise
    """
    cloud_type = read_config("cloud", "cloud_type")
    try:
        if cloud_type == "local":
            return True
        elif cloud_type == "aws":
            return item1.split(".")[0] == item2.split(".")[0]
        elif cloud_type == "gcp":
            return item1.split("-")[0] == item2.split("-")[0]
        elif cloud_type == "azure":
            return extract_prefix_and_number(item1) == extract_prefix_and_number(item2)
    except Exception as exc:
        custom_logger.error(f"Error comparing instances {item1} and {item2}: {exc}")
        return False


# Compare the pyperf results from multiple spreadsheets
def compare_pyperf_results(spreadsheets, spreadsheetId, test_name, table_name=["System name", "Price-perf"]):
    """
    Compare and merge benchmark results from multiple spreadsheets and append the results to the given sheet.

    Args:
        spreadsheets (list): List of spreadsheet IDs to compare
        spreadsheetId (str): Spreadsheet ID where the result should be saved
        test_name (str): Name of the test (e.g., "pyperf")
        table_name (list): List of table names to compare (default: ["System name", "Price-perf"])

    Returns:
        str: The spreadsheet ID if the operation was successful
    """
    values = []
    results = []
    spreadsheet_names = []

    # Read data from all spreadsheets
    try:
        for spreadsheet in spreadsheets:
            values.append(read_sheet(spreadsheet, range=test_name))
            spreadsheet_names.append(get_sheet(spreadsheet, test_name=test_name)["properties"]["title"])
    except Exception as exc:
        custom_logger.error(f"Error reading sheets: {exc}")
        return spreadsheetId

    # Group values by non-empty rows
    for index, value in enumerate(values):
        values[index] = (list(g) for k, g in groupby(value, key=lambda x: x != []) if k)
    list_1 = list(values[0])
    list_2 = list(values[1])

    # Compare and merge data from both sheets
    for value in list_1:
        for ele in list_2:
            # Check max throughput or cost/hr and compare
            if value[0][0] in table_name and ele[0][0] in table_name and value[0][0] == ele[0][0]:
                if compare_inst(value[1][0], ele[1][0]):
                    results.append([""])
                    header = []
                    data = []
                    for item1 in value:
                        for item2 in ele:
                            if item1[0] == item2[0]:
                                if item1[0] in table_name:
                                    header = merge_lists_alternately(header, item1, item2)
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

            elif value[1][0] == ele[1][0]:
                if value[0][0] == ele[0][0]:
                    results.append([""])
                    results.append(value[0])
                    for item1, item2 in zip(value[1:], ele[1:]):
                        results = merge_lists_alternately(results, item1, item2)
                    break

    # Write the results back to the sheet
    try:
        create_sheet(spreadsheetId, test_name)
        custom_logger.info("Deleting existing charts and data from the sheet...")
        clear_sheet_charts(spreadsheetId, test_name)
        clear_sheet_data(spreadsheetId, test_name)
        custom_logger.info(f"Appending new {test_name} data to sheet...")
        append_to_sheet(spreadsheetId, results, test_name)
    except Exception as exc:
        custom_logger.debug(f"Error during sheet operations: {exc}")
        custom_logger.error("Failed to append data to sheet")
        return spreadsheetId

    return spreadsheetId


if __name__ == "__main__":
    # List of spreadsheets to compare
    spreadsheets = [
        "",  # Replace with actual spreadsheet IDs
        "",  # Replace with actual spreadsheet IDs
    ]
    test_name = "pyperf"

    # Compare results and update the sheet
    compare_pyperf_results(spreadsheets, "", test_name, table_name=["System name"])
