import time

from quisby.formatting.add_formatting import update_conditional_formatting
from quisby.sheet.sheet_util import read_sheet, get_sheet, append_empty_row_sheet
from quisby.sheet.sheetapi import sheet
from quisby.util import read_value


def create_series_range_pig_process(column_count, sheetId, start_index, end_index):
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


def create_series_range_pig_compare(column_count, sheetId, start_index, end_index):
    """"""
    series = [
        {
            "series": {
                "sourceRange": {
                    "sources": [
                        {
                            "sheetId": sheetId,
                            "startRowIndex": start_index+1,
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
                            "sheetId": sheetId,
                            "startRowIndex": start_index+1,
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
                            "sheetId": sheetId,
                            "startRowIndex": start_index+1,
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


def graph_pig_data(spreadsheetId, test_name, action):
    """"""
    GRAPH_COL_INDEX = 1
    GRAPH_ROW_INDEX = 0
    start_index, end_index = None,None
    sheetId = -1

    data = read_sheet(spreadsheetId, test_name)

    if len(data) > 500:
        append_empty_row_sheet(spreadsheetId, 3000, test_name)

    diff_col = [3]

    for index, row in enumerate(data):
        if "Threads" in row:
            start_index = index - 1

        if start_index:
            if not row:
                end_index = index
            elif index + 1 == len(data):
                end_index = index + 1

        if end_index:
            graph_data = data[start_index:end_index]
            column_count = len(graph_data[1])

            sheetId = get_sheet(spreadsheetId, test_name)["sheets"][0]["properties"][
                "sheetId"
            ]

            series = globals()[f'create_series_range_pig_{action}'](column_count, sheetId, start_index, end_index)

            requests = {
                "addChart": {
                    "chart": {
                        "spec": {
                            "title": f"{test_name}",
                            "subtitle": f"{graph_data[0][0]}",
                            "basicChart": {
                                "chartType": "COMBO",
                                "legendPosition": "RIGHT_LEGEND",
                                "axis": [
                                    {"position": "BOTTOM_AXIS", "title": "Threads"},
                                    {
                                        "position": "LEFT_AXIS",
                                        "title": "Scheduler Efficiency",
                                    },
                                    {
                                        "position": "RIGHT_AXIS",
                                        "title": "%Diff",
                                    },
                                ],
                                "domains": [
                                    {
                                        "domain": {
                                            "sourceRange": {
                                                "sources": [
                                                    {
                                                        "sheetId": sheetId,
                                                        "startRowIndex": start_index+1,
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

    if sheetId != -1:
        threshold = read_value("percent_threshold", test_name)
        if not threshold:
            threshold = "5"
        for col in diff_col:
            update_conditional_formatting(spreadsheetId, sheetId, col, threshold)