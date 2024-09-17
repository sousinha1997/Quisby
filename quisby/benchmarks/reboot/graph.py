import time

from quisby.sheet.sheetapi import sheet
from quisby.sheet.sheet_util import read_sheet, get_sheet,append_empty_row_sheet


def create_series_range_boot(column_count, sheetId, start_index, end_index):
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


def graph_boot_data(spreadsheetId, test_name, action):
    GRAPH_COL_INDEX = 1
    GRAPH_ROW_INDEX = 0
    start_index, end_index = None, None

    data = read_sheet(spreadsheetId, test_name)
    if len(data) > 500:
        append_empty_row_sheet(spreadsheetId, 3000, test_name)

    for index, row in enumerate(data):
        if row[0] == "System name" and start_index is None:
            start_index = index
            continue

        if start_index is not None:
            if index + 1 == len(data):
                end_index = index + 1
            elif data[index + 1][0] == "System name":
                end_index = index + 1

        if end_index:
            graph_data = data[start_index:end_index]
            column_count = len(graph_data[0])

            sheetId = get_sheet(spreadsheetId, test_name)["sheets"][0]["properties"][
                "sheetId"
            ]
            subtitle = graph_data[1][0].split(".")[0]
            requests = {
                "addChart": {
                    "chart": {
                        "spec": {
                            "title": f"Instance {test_name} time",
                            "subtitle": f"{subtitle}",
                            "basicChart": {
                                "chartType": "COLUMN",
                                "legendPosition": "RIGHT_LEGEND",
                                "axis": [
                                    {
                                        "format": {
                                            "bold": True,
                                            "italic": True,
                                            "fontSize": 14
                                        },
                                        "position": "BOTTOM_AXIS",
                                        "title": "System"},
                                    {
                                        "format": {
                                            "bold": True,
                                            "italic": True,
                                            "fontSize": 14
                                        },
                                        "position": "LEFT_AXIS",
                                        "title": "Time(secs)",
                                    },
                                ],
                                "domains": [
                                    {
                                        "domain": {
                                            "sourceRange": {
                                                "sources": [
                                                    {
                                                        "sheetId": sheetId,
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
                                "series": create_series_range_boot(
                                    column_count, sheetId, start_index, end_index
                                ),
                                "headerCount": 1,
                            },
                        },
                        "position": {
                            "overlayPosition": {
                                "anchorCell": {
                                    "sheetId": sheetId,
                                    "rowIndex": GRAPH_ROW_INDEX,
                                    "columnIndex": column_count + GRAPH_COL_INDEX,
                                },
                                "offsetXPixels": 100,
                                "widthPixels": 600,
                                "heightPixels": 400
                            }
                        },
                    }
                }
            }
            if GRAPH_COL_INDEX >= 5:
                GRAPH_ROW_INDEX += 20
                GRAPH_COL_INDEX = 1
            else:
                GRAPH_COL_INDEX += 6

            body = {"requests": requests}

            sheet.batchUpdate(spreadsheetId=spreadsheetId, body=body).execute()

            start_index, end_index = None, None

            time.sleep(3)