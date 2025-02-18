import logging
from typing import List, Optional, Tuple

from itertools import groupby

from quisby import custom_logger
from quisby.benchmarks.coremark.graph import graph_coremark_data
from quisby.sheet.sheet_util import (
    append_to_sheet,
    clear_sheet_charts,
    clear_sheet_data,
    create_sheet,
    get_sheet,
    read_sheet
)
from quisby.util import merge_lists_alternately


def read_spreadsheet_data(
        spreadsheet_id: str,
        test_name: str
) -> Tuple[List[List], str]:
    """
    Read data from a spreadsheet and extract its title.

    Args:
        spreadsheet_id (str): ID of the spreadsheet
        test_name (str): Name of the test/sheet

    Returns:
        Tuple of (spreadsheet data, spreadsheet title)
    """
    try:
        sheet_data = read_sheet(spreadsheet_id, range=test_name)
        sheet_info = get_sheet(spreadsheet_id, test_name=test_name)
        spreadsheet_title = sheet_info["properties"]["title"]

        # Filter out empty rows and group data
        filtered_data = [list(g) for k, g in groupby(sheet_data, key=lambda x: x != []) if k]

        return filtered_data, spreadsheet_title
    except Exception as exc:
        custom_logger.error(f"Error reading spreadsheet {spreadsheet_id}: {exc}")
        raise


def compare_spreadsheet_data(
        data_lists: List[List],
        table_names: List[str] = ["System name"]
) -> List[List]:
    """
    Compare data from multiple spreadsheets.

    Args:
        data_lists (List[List]): List of spreadsheet data to compare
        table_names (List[str], optional): Column names to match. Defaults to ["System name"]

    Returns:
        List of merged comparison results
    """
    results = []

    # Unpack the first two spreadsheets for comparison
    list_1, list_2 = data_lists[0], data_lists[1]

    for value in list_1:
        for ele in list_2:
            # Check for matching table names or system names
            if (value[0][0] in table_names and ele[0][0] in table_names) or \
                    (value[1][0] == ele[1][0] and value[0][0] == ele[0][0]):

                results.append([""])

                # Add headers
                if value[0][0] in table_names:
                    results.extend(merge_lists_alternately([], value[0], ele[0]))
                else:
                    results.append(value[0])

                # Merge data rows
                for item1, item2 in zip(value[1:], ele[1:]):
                    results = merge_lists_alternately(results, item1, item2)

                break

    return results


def compare_coremark_results(
        spreadsheets: List[str],
        spreadsheet_id: str,
        test_name: str,
        table_names: List[str] = ["System name"]
) -> Optional[str]:
    """
    Compare CoreMark results across multiple spreadsheets.

    Args:
        spreadsheets (List[str]): List of spreadsheet IDs to compare
        spreadsheet_id (str): Target spreadsheet ID to save results
        test_name (str): Name of the test/sheet
        table_names (List[str], optional): Column names to match. Defaults to ["System name"]

    Returns:
        Spreadsheet ID or None
    """
    try:
        # Read data from each spreadsheet
        spreadsheet_data = [
            read_spreadsheet_data(spreadsheet, test_name)[0]
            for spreadsheet in spreadsheets
        ]

        # Compare results
        comparison_results = compare_spreadsheet_data(spreadsheet_data, table_names)

        # Update target spreadsheet
        create_sheet(spreadsheet_id, test_name)

        custom_logger.info("Deleting existing charts and data from the sheet...")
        clear_sheet_charts(spreadsheet_id, test_name)
        clear_sheet_data(spreadsheet_id, test_name)

        custom_logger.info(f"Appending new {test_name} data to sheet...")
        append_to_sheet(spreadsheet_id, comparison_results, test_name)

        # Optional: Uncomment to create graph
        # graph_coremark_data(spreadsheet_id, test_name, "compare")

        return spreadsheet_id

    except Exception as exc:
        custom_logger.error(f"Failed to compare CoreMark results: {exc}")
        custom_logger.debug(str(exc), exc_info=True)
        return None


if __name__ == "__main__":
    # Example usage with placeholder values
    spreadsheets = [
        "spreadsheet_id_1",
        "spreadsheet_id_2"
    ]
    target_spreadsheet_id = "target_spreadsheet_id"
    test_name = "coremark"

    result = compare_coremark_results(
        spreadsheets,
        target_spreadsheet_id,
        test_name,
        table_names=["System Name"]
    )

    if result:
        print(f"Comparison completed successfully: {result}")
    else:
        print("Comparison failed")