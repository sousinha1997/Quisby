from itertools import groupby
import re
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
    Extract the prefix and suffix from an instance name that includes a number.
    Example: "t2.micro-01" => ("t2.micro", "01")
    """
    match = re.search(r'^(.*?)(\d+)(.*?)$', input_string)
    if match:
        prefix = match.group(1)
        suffix = match.group(3)  # Extracts the suffix after the number
        return prefix, suffix
    return None, None


# Helper function to compare instance names based on cloud type
def compare_inst(item1, item2):
    """
    Compare two instance names based on the cloud type.
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


# Function to compare PassMark results between two spreadsheets
def compare_passmark_results(spreadsheets, spreadsheetId, test_name, table_name=["System name", "Price-perf"]):
    """
    Compare PassMark benchmark data between two Google Sheets.
    The data is merged and appended to the target sheet.
    """
    values = []
    results = []
    spreadsheet_name = []

    # Read data from each spreadsheet
    for spreadsheet in spreadsheets:
        values.append(read_sheet(spreadsheet, range=test_name))
        spreadsheet_name.append(get_sheet(spreadsheet, test_name=test_name)["properties"]["title"])

    # Group values into segments (non-empty groups)
    for index, value in enumerate(values):
        values[index] = (list(g) for k, g in groupby(value, key=lambda x: x != []) if k)

    list_1 = list(values[0])
    list_2 = list(values[1])

    # Merge the results by comparing each value and adding to the final results
    for value in list_1:
        for ele in list_2:
            # Compare system name and price-perf
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
            # Compare cost per hour
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
            # Compare other matching rows
            elif value[1][0] == ele[1][0]:
                if value[0][0] == ele[0][0]:
                    results.append([""])
                    results.append(value[0])
                    for item1, item2 in zip(value[1:], ele[1:]):
                        results = merge_lists_alternately(results, item1, item2)
                    break

    # Create the sheet and append the merged results
    try:
        create_sheet(spreadsheetId, test_name)
        custom_logger.info("Deleting existing charts and data from the sheet...")
        clear_sheet_charts(spreadsheetId, test_name)
        clear_sheet_data(spreadsheetId, test_name)
        custom_logger.info(f"Appending new {test_name} data to sheet...")
        append_to_sheet(spreadsheetId, results, test_name)
    except Exception as exc:
        custom_logger.debug(str(exc))
        custom_logger.error("Failed to append data to sheet")
        return spreadsheetId


# Main execution block
if __name__ == "__main__":
    spreadsheets = [
        "spreadsheet_id_1",  # Replace with actual spreadsheet ID
        "spreadsheet_id_2",  # Replace with actual spreadsheet ID
    ]
    test_name = "passmark"

    # Compare the PassMark results from two spreadsheets
    compare_passmark_results(spreadsheets, "spreadsheet_id_1", test_name, table_name=["SYSTEM_NAME"])
