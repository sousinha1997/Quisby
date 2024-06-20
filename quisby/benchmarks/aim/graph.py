import time

from quisby.sheet.sheetapi import sheet
from quisby.sheet.sheet_util import read_sheet, clear_sheet_charts, get_sheet,append_empty_row_sheet


def create_series_range_aim(column_count, sheetId, start_index, end_index):
    """"""
    series = []

    for index in range(column_count):

        series.append(
            {
                "series": {
                    "sourceRange": {
                        "sources": [
                            {
                                "sheetId": sheetId,
                                "startRowIndex": start_index + 2,
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


def graph_aim_data(spreadsheetId, test_name, action):
    """"""
    GRAPH_COL_INDEX = 5
    GRAPH_ROW_INDEX = 1
    start_index, end_index = None, None

    data = read_sheet(spreadsheetId, test_name)
    if len(data) > 500:
        append_empty_row_sheet(spreadsheetId, 3000, test_name)

    for index, row in enumerate(data):
        if row == [] and start_index is None:
            start_index = index
            continue

        if start_index is not None:
            if index + 1 == len(data):
                end_index = index + 1
            elif data[index + 1] == []:
                end_index = index

        if end_index:
            graph_data = data[start_index:end_index]
            column_count = len(graph_data[2])

            sheetId = get_sheet(spreadsheetId, test_name)["sheets"][0]["properties"][
                "sheetId"
            ]

            requests = {
                "addChart": {
                    "chart": {
                        "spec": {
                            "title": f"aim 7 {graph_data[1][0]}",
                            "subtitle": f"{graph_data[1][1]}",
                            "basicChart": {
                                "chartType": "LINE",
                                "axis": [
                                    {
                                        "position": "LEFT_AXIS",
                                        "title": "jobs/min",
                                    },
                                    {
                                        "position": "BOTTOM_AXIS",
                                        "title": "Load"
                                    }
                                ],
                                "domains": [
                                    {
                                        "domain": {
                                            "sourceRange": {
                                                "sources": [
                                                    {
                                                        "sheetId": sheetId,
                                                        "startRowIndex": start_index
                                                        + 2,
                                                        "endRowIndex": end_index + 1,
                                                        "startColumnIndex": 0,
                                                        "endColumnIndex": 1,
                                                    }
                                                ]
                                            }
                                        }
                                    }
                                ],
                                "series": create_series_range_aim(
                                    column_count, sheetId, start_index, end_index + 1
                                ),
                                "headerCount": 1,
                            },
                        },
                        "position": {
                            "overlayPosition": {
                                "anchorCell": {
                                    "sheetId": sheetId,
                                    "rowIndex": GRAPH_ROW_INDEX,
                                    "columnIndex": GRAPH_COL_INDEX,
                                }
                            }
                        },
                    }
                }
            }
            if GRAPH_COL_INDEX >= 6:
                GRAPH_ROW_INDEX += 20
                GRAPH_COL_INDEX = 5
            else:
                GRAPH_COL_INDEX += 6

            body = {"requests": requests}

            sheet.batchUpdate(spreadsheetId=spreadsheetId, body=body).execute()

            start_index, end_index = None, None

            time.sleep(3)