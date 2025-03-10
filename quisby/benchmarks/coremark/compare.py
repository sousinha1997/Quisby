from quisby import custom_logger
from itertools import groupby
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
    Extracts the prefix and suffix from an instance name that contains a number.

    :param input_string: Instance name, e.g., 't2.micro-01'
    :return: Tuple (prefix, suffix) or (None, None) if no match
    """
    try:
        match = re.search(r'^(.*?)(\d+)(.*?)$', input_string)
        if match:
            prefix = match.group(1)
            suffix = match.group(3)  # Extracts the suffix after the number
            return prefix, suffix
    except Exception as exc:
        custom_logger.error(f"Error extracting prefix and number from '{input_string}': {str(exc)}")
    return None, None


def compare_inst(item1, item2):
    """
    Compares two instance names based on the cloud provider's convention.

    :param item1: Instance name from the first spreadsheet
    :param item2: Instance name from the second spreadsheet
    :return: True if instance names are considered the same, False otherwise
    """
    try:
        cloud_type = read_config("cloud", "cloud_type")
        if cloud_type == "local":
            return True
        elif cloud_type == "aws":
            return item1.split(".")[0] == item2.split(".")[0]
        elif cloud_type == "gcp":
            return item1.split("-")[0] == item2.split("-")[0]
        elif cloud_type == "azure":
            return extract_prefix_and_number(item1) == extract_prefix_and_number(item2)
    except Exception as exc:
        custom_logger.error(f"Error comparing instances '{item1}' and '{item2}': {str(exc)}")
    return False


def compare_coremark_results(spreadsheets, spreadsheetId, test_name, table_name=["System name", "Price-perf"]):
    """
    Compares CoreMark results from multiple spreadsheets and appends the merged data to the target sheet.

    :param spreadsheets: List of spreadsheet names to compare
    :param spreadsheetId: Target spreadsheet ID for appending data
    :param test_name: The name of the test to compare (e.g., 'coremark')
    :param table_name: List of columns to compare (default ["System name", "Price-perf"])
    """
    try:
        values = []
        results = []
        spreadsheet_name = []

        # Read data from each spreadsheet
        for spreadsheet in spreadsheets:
            values.append(read_sheet(spreadsheet, range=test_name))
            spreadsheet_name.append(get_sheet(spreadsheet, test_name=test_name)["properties"]["title"])

        # Group the values into non-empty chunks
        for index, value in enumerate(values):
            values[index] = (list(g) for k, g in groupby(value, key=lambda x: x != []) if k)

        list_1 = list(values[0])
        list_2 = list(values[1])

        # Compare the CoreMark results from both spreadsheets
        for value in list_1:
            for ele in list_2:
                # Check max throughput or other table data
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
                # Handle cost/hour comparison
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
                # General comparison based on row keys
                elif value[1][0] == ele[1][0]:
                    if value[0][0] == ele[0][0]:
                        results.append([""])
                        results.append(value[0])
                        for item1, item2 in zip(value[1:], ele[1:]):
                            results = merge_lists_alternately(results, item1, item2)
                        break

        # Try to append the merged data to the target sheet
        try:
            create_sheet(spreadsheetId, test_name)
            custom_logger.info(f"Deleting existing charts and data from the sheet '{test_name}'...")
            clear_sheet_charts(spreadsheetId, test_name)
            clear_sheet_data(spreadsheetId, test_name)
            custom_logger.info(f"Appending new {test_name} data to sheet...")
            append_to_sheet(spreadsheetId, results, test_name)
        except Exception as exc:
            custom_logger.error(f"Failed to append data to sheet '{test_name}' in spreadsheet {spreadsheetId}: {str(exc)}")
            return spreadsheetId
    except Exception as exc:
        custom_logger.error(f"Error comparing CoreMark results: {str(exc)}")


if __name__ == "__main__":
    # Example usage with empty spreadsheet list and target spreadsheetId
    spreadsheets = [
        "",  # Add first spreadsheet ID
        "",  # Add second spreadsheet ID
    ]
    test_name = "coremark"

    # Call the function to compare the results and update the sheet
    compare_coremark_results(spreadsheets, "", test_name, table_name=["System Name"])
