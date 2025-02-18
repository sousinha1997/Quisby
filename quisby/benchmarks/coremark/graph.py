from typing import Dict, List, Optional

from quisby.formatting.add_formatting import update_conditional_formatting
from quisby.sheet.sheet_util import (
    append_empty_row_sheet,
    clear_sheet_charts,
    get_sheet,
    read_sheet
)
from quisby.sheet.sheetapi import sheet
from quisby.util import read_value

import time


def create_series_range_list_coremark_process(
        column_count: int,
        sheet_id: int,
        start_index: int,
        end_index: int
) -> List[Dict]:
    """
    Create series range list for CoreMark processing graph.

    Args:
        column_count (int): Number of columns in the data
        sheet_id (int): ID of the Google Sheet
        start_index (int): Starting row index
        end_index (int): Ending row index

    Returns:
        List of series configuration dictionaries
    """
    return [
        {
            "series": {
                "sourceRange": {
                    "sources": [{
                        "sheetId": sheet_id,
                        "startRowIndex": start_index,
                        "endRowIndex": end_index,
                        "startColumnIndex": index + 1,
                        "endColumnIndex": index + 2,
                    }]
                },
            },
            "type": "COLUMN",
        }
        for index in range(column_count)
    ]


def create_series_range_list_coremark_compare(
        column_count: int,
        sheet_id: int,
        start_index: int,
        end_index: int
) -> List[Dict]:
    """
    Create series range list for CoreMark comparison graph.

    Args:
        column_count (int): Number of columns in the data
        sheet_id (int): ID of the Google Sheet
        start_index (int): Starting row index
        end_index (int): Ending row index

    Returns:
        List of series configuration dictionaries
    """
    return [
        {
            "series": {
                "sourceRange": {
                    "sources": [{
                        "sheetId": sheet_id,
                        "startRowIndex": start_index,
                        "endRowIndex": end_index,
                        "startColumnIndex": col_index,
                        "endColumnIndex": col_index + 1,
                    }]
                }
            },
            "targetAxis": "LEFT_AXIS" if col_index < 2 else "RIGHT_AXIS",
            "type": "COLUMN" if col_index < 2 else "LINE",
        }
        for col_index in range(3)
    ]


def graph_coremark_data(
        spreadsheet_id: str,
        data_range: str,
        action: str
) -> None:
    """
    Generate graphs for CoreMark performance data.

    Args:
        spreadsheet_id (str): Google Sheets spreadsheet identifier
        data_range (str): Range of data to graph
        action (str): Type of graph to create (process or compare)
    """
    GRAPH_INITIAL_COL_INDEX = 1
    GRAPH_INITIAL_ROW_INDEX = 1
    DIFF_COLUMNS = [3]

    # Read sheet data
    data = read_sheet(spreadsheet_id, data_range)

    # Ensure enough space in sheet
    if len(data) > 500:
        append_empty_row_sheet(spreadsheet_id, 3000, data_range)

    # Variables for tracking graph creation
    graph_col_index = GRAPH_INITIAL_COL_INDEX
    graph_row_index = GRAPH_INITIAL_ROW_INDEX
    start_index = 0
    end_index = 0
    sheet_id = -1

    # Process data and create graphs
    for index, row in enumerate(data):
        # Find header and data range
        if "System name" in row:
            start_index = index

        if start_index:
            # Determine end of data section
            if not row or index + 1 == len(data):
                end_index = index + 1

        if end_index:
            graph_data = data[start_index:end_index]
            column_count = len(graph_data[0])

            # Get sheet ID
            sheet_id = get_sheet(spreadsheet_id, data_range)["sheets"][0]["properties"]["sheetId"]

            # Create series based on action
            series_creator = globals()[f'create_series_range_list_coremark_{action}']
            series = series_creator(column_count, sheet_id, start_index, end_index)

            # Prepare chart request
            chart_request = {
                "addChart": {
                    "chart": {
                        "spec": {
                            "title": f"{data_range} : Test passes",
                            "basicChart": {
                                "chartType": "COMBO",
                                "legendPosition": "BOTTOM_LEGEND",
                                "axis": [
                                    {"position": "LEFT_AXIS", "title": "Test passes"},
                                    {"position": "BOTTOM_AXIS", "title": "Machine types"},
                                    {"position": "RIGHT_AXIS", "title": "%Diff"},
                                ],
                                "domains": [{
                                    "domain": {
                                        "sourceRange": {
                                            "sources": [{
                                                "sheetId": sheet_id,
                                                "startRowIndex": start_index,
                                                "endRowIndex": end_index,
                                                "startColumnIndex": 0,
                                                "endColumnIndex": 1,
                                            }]
                                        }
                                    }
                                }],
                                "series": series,
                                "headerCount": 1,
                            },
                        },
                        "position": {
                            "overlayPosition": {
                                "anchorCell": {
                                    "sheetId": sheet_id,
                                    "rowIndex": graph_row_index,
                                    "columnIndex": column_count + 1,
                                }
                            }
                        },
                    }
                }
            }

            # Adjust graph positioning
            if graph_col_index >= 5:
                graph_row_index += 20
                graph_col_index = 1
            else:
                graph_col_index += 6

            # Execute chart creation
            sheet.batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": chart_request}).execute()

            # Reset for next iteration
            start_index, end_index = 0, 0
            time.sleep(3)

    # Add conditional formatting for difference columns
    if sheet_id != -1:
        threshold = read_value("percent_threshold", data_range) or "5"
        for col in DIFF_COLUMNS:
            update_conditional_formatting(spreadsheet_id, sheet_id, col, threshold)


if __name__ == "__main__":
    # Example usage with placeholder values
    graph_coremark_data("spreadsheet_id", "data_range", "process")