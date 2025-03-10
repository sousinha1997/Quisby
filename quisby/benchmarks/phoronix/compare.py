from itertools import groupby

from quisby import custom_logger
from quisby.benchmarks.phoronix.graph import graph_phoronix_data
from quisby.sheet.sheet_util import (
    append_to_sheet,
    read_sheet,
    get_sheet,
    create_sheet,
    clear_sheet_data,
    clear_sheet_charts,
)
from quisby.util import merge_lists_alternately, read_config
import re


def extract_prefix_and_number(input_string):
    """
    Extracts the prefix and suffix of an instance identifier, separating the numeric part.

    Args:
        input_string (str): The instance identifier string.

    Returns:
        tuple: The prefix and suffix extracted from the identifier.
    """
    match = re.search(r'^(.*?)(\d+)(.*?)$', input_string)
    if match:
        prefix = match.group(1)
        suffix = match.group(3)  # Extracts the suffix after the number
        return prefix, suffix
    return None, None


def compare_inst(item1, item2):
    """
    Compares two instance identifiers based on the cloud type.

    Args:
        item1 (str): First instance identifier.
        item2 (str): Second instance identifier.

    Returns:
        bool: True if the instances match based on the cloud type, else False.
    """
    cloud_type = read_config("cloud", "cloud_type")
    if cloud_type == "local":
        return True
    elif cloud_type == "aws":
        return item1.split(".")[0] == item2.split(".")[0]
    elif cloud_type == "gcp":
        return item1.split("-")[0] == item2.split("-")[0]
    elif cloud_type == "azure":
        return extract_prefix_and_number(item1) == extract_prefix_and_number(item2)


def compare_phoronix_results(spreadsheets, spreadsheetId, test_name, table_name=["System name", "Price-perf"]):
    """
    Compares performance results from multiple spreadsheets for a given test.

    Args:
        spreadsheets (list): List of spreadsheet identifiers.
        spreadsheetId (str): The spreadsheet ID to append results to.
        test_name (str): The name of the test being compared.
        table_name (list): List of table names to compare.

    Returns:
        str: The spreadsheetId after appending the data.
    """
    values = []
    results = []
    spreadsheet_name = []

    # Read the data from each spreadsheet
    for spreadsheet in spreadsheets:
        values.append(read_sheet(spreadsheet, range=test_name))
        spreadsheet_name.append(get_sheet(spreadsheet, test_name=test_name)["properties"]["title"])

    # Group values to segregate by test groups
    for index, value in enumerate(values):
        values[index] = (list(g) for k, g in groupby(value, key=lambda x: x != []) if k)

    list_1 = list(values[0])
    list_2 = list(values[1])

    # Compare the grouped values from both spreadsheets
    for value in list_1:
        for ele in list_2:
            # Check for matching table name and instance comparison
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

            # Special case for "Cost/Hr" data
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

            # Compare other data that matches based on instance identifier
            elif value[1][0] == ele[1][0]:
                if value[0][0] == ele[0][0]:
                    results.append([""])
                    results.append(value[0])
                    for item1, item2 in zip(value[1:], ele[1:]):
                        results = merge_lists_alternately(results, item1, item2)
                    break

    try:
        # Create a new sheet and append the results
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


if __name__ == "__main__":
    # List of spreadsheet IDs to compare
    spreadsheets = [
        "spreadsheet_id_1",
        "spreadsheet_id_2",
    ]
    test_name = "phoronix"

    # Generate and graph the Phoronix benchmark data
    graph_phoronix_data(spreadsheets, "output_path", test_name, table_name=["SYSTEM_NAME"])
