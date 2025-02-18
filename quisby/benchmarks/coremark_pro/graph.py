import time

from quisby.formatting.add_formatting import update_conditional_formatting
from quisby.sheet.sheet_util import read_sheet, get_sheet, append_empty_row_sheet
from quisby.sheet.sheetapi import sheet
from quisby.util import read_value


def create_series_range_list_coremark_pro_process(column_count, sheet_id, start_index, end_index):
    """
    Create a series range list for processing Coremark Pro data.

    Args:
        column_count (int): The number of columns in the data.
        sheet_id (int): The sheet ID.
        start_index (int): The start row index.
        end_index (int): The end row index.

    Returns:
        list: A list of series configuration for chart creation.
    """
    series = []

    for index in range(column_count):
        series.append(
            {
                "series": {
                    "sourceRange": {
                        "sources": [
                            {
                                "sheetId": sheet_id,
                                "startRowIndex": start_index,
                                "endRowIndex": end_index,
                                "startColumnIndex": index + 1,
                                "endColumnIndex": index + 2,
                            }
                        ]
                    }
                },
                "type": "COLUMN",
            }
        )

    return series


def create_series_range_list_coremark_pro_compare(column_count, sheet_id, start_index, end_index):
    """
    Create a series range list for comparing Coremark Pro data.

    Args:
        column_count (int): The number of columns in the data.
        sheet_id (int): The sheet ID.
        start_index (int): The start row index.
        end_index (int): The end row index.

    Returns:
        list: A list of series configuration for chart creation.
    """
    series = [
        {
            "series": {
                "sourceRange": {
                    "sources": [
                        {
                            "sheetId": sheet_id,
                            "startRowIndex": start_index,
                            "endRowIndex": end_index,
                            "startColumnIndex": 1,
                            "endColumnIndex": 2,
                        }
                    ]
                }
            },
            "targetAxis": "LEFT_AXIS",
            "type": "COLUMN",
        },
        {
            "series": {
                "sourceRange": {
                    "sources": [
                        {
                            "sheetId": sheet_id,
                            "startRowIndex": start_index,
                            "endRowIndex": end_index,
                            "startColumnIndex": 2,
                            "endColumnIndex": 3,
                        }
                    ]
                }
            },
            "targetAxis": "LEFT_AXIS",
            "type": "COLUMN",
        },
        {
            "series": {
                "sourceRange": {
                    "sources": [
                        {
                            "sheetId": sheet_id,
                            "startRowIndex": start_index,
                            "endRowIndex": end_index,
                            "startColumnIndex": 3,
                            "endColumnIndex": 4,
                        }
                    ]
                }
            },
            "targetAxis": "RIGHT_AXIS",
            "type": "LINE",
        },
    ]
    return series


def graph_coremark_pro_data(spreadsheet_id, data_range, action):
    """
    Generate and insert a graph for Coremark Pro data into the specified spreadsheet.

    Args:
        spreadsheet_id (str): The ID of the spreadsheet.
        data_range (str): The range of data to graph.
        action (str): The action type, either 'process' or 'compare'.

    """
    GRAPH_COL_INDEX = 1
    GRAPH_ROW_INDEX = 1
    start_index = 0
    end_index = 0
    diff_col = [3]

    data = read_sheet(spreadsheet_id, data_range)

    if len(data) > 500:
        append_empty_row_sheet(spreadsheet_id, 3000, data_range)

    header = []
    sheet_id = -1

    for index, row in enumerate(data):
        if "System name" in row:
            start_index = index
            iteration = data[index - 1][0]
            header.extend(row)
        if start_index:
            if not row:
                end_index = index
            if index + 1 == len(data):
                end_index = index + 1

        if end_index:
            graph_data = data[start_index:end_index]
            column_count = len(graph_data[0])

            sheet_id = get_sheet(spreadsheet_id, data_range)["sheets"][0]["properties"][
                "sheetId"
            ]

            series = globals()[f'create_series_range_list_coremark_pro_{action}'](column_count, sheet_id, start_index, end_index)

            requests = {
                "addChart": {
                    "chart": {
                        "spec": {
                            "title": f"{data_range} : score : {iteration}",
                            "basicChart": {
                                "chartType": "COMBO",
                                "legendPosition": "BOTTOM_LEGEND",
                                "axis": [
                                    {"position": "BOTTOM_AXIS", "title": ""},
                                    {"position": "LEFT_AXIS", "title": "Score"},
                                    {"position": "RIGHT_AXIS", "title": "%Diff"},
                                ],
                                "domains": [
                                    {
                                        "domain": {
                                            "sourceRange": {
                                                "sources": [
                                                    {
                                                        "sheetId": sheet_id,
                                                        "startRowIndex": start_index,
                                                        "endRowIndex": end_index,
                                                        "startColumnIndex": 0,
                                                        "endColumnIndex": 1,
                                                    }
                                                ]
                                            }
                                        }
                                    }
                                ],
                                "series": series,
                                "headerCount": 1,
                            },
                        },
                        "position": {
                            "overlayPosition": {
                                "anchorCell": {
                                    "sheetId": sheet_id,
                                    "rowIndex": GRAPH_ROW_INDEX,
                                    "columnIndex": column_count + GRAPH_COL_INDEX,
                                }
                            }
                        },
                    }
                }
            }

            if GRAPH_COL_INDEX >= 5:
                GRAPH_ROW_INDEX += 20
                GRAPH_COL_INDEX = 1
            else:
                GRAPH_ROW_INDEX = end_index

            body = {"requests": requests}

            sheet.batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()

            # Reset variables
            start_index, end_index = 0, 0

            time.sleep(3)

    if sheet_id != -1:
        threshold = read_value("percent_threshold", data_range)
        if not threshold:
            threshold = "5"
        for col in diff_col:
            update_conditional_formatting(spreadsheet_id, sheet_id, col, threshold)
