import time

from quisby.sheet.sheetapi import sheet
from quisby.sheet.sheet_util import read_sheet, clear_sheet_charts, get_sheet


def create_series_range_pig(column_count, sheetId, start_index, end_index):
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
                                "startRowIndex": start_index + 1,
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


def graph_pig_data(spreadsheetId, test_name):
    """"""
    GRAPH_COL_INDEX = 1
    GRAPH_ROW_INDEX = 0
    start_index, end_index = None, None

    data = read_sheet(spreadsheetId, test_name)

    for index, row in enumerate(data):
        if "Threads" in row:
            start_index = index - 1

        if start_index:
            if row == []:
                end_index = index
            elif index + 1 == len(data):
                end_index = index + 1

        if end_index:
            graph_data = data[start_index:end_index]
            column_count = len(graph_data[1])

            sheetId = get_sheet(spreadsheetId, test_name)["sheets"][0]["properties"][
                "sheetId"
            ]

            requests = {
                "addChart": {
                    "chart": {
                        "spec": {
                            "title": f"{test_name}",
                            "subtitle": f"{graph_data[0][0]}",
                            "basicChart": {
                                "chartType": "COLUMN",
                                "legendPosition": "BOTTOM_LEGEND",
                                "axis": [
                                    {"position": "BOTTOM_AXIS", "title": "Threads"},
                                    {
                                        "position": "LEFT_AXIS",
                                        "title": "Scheduler Efficiency",
                                    },
                                ],
                                "domains": [
                                    {
                                        "domain": {
                                            "sourceRange": {
                                                "sources": [
                                                    {
                                                        "sheetId": sheetId,
                                                        "startRowIndex": start_index
                                                        + 1,
                                                        "endRowIndex": end_index,
                                                        "startColumnIndex": 0,
                                                        "endColumnIndex": 1,
                                                    }
                                                ]
                                            }
                                        }
                                    }
                                ],
                                "series": create_series_range_pig(
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
                GRAPH_COL_INDEX += 6

            body = {"requests": requests}

            sheet.batchUpdate(spreadsheetId=spreadsheetId, body=body).execute()

            start_index, end_index = None, None

            time.sleep(3)
