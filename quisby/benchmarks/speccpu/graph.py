import time

from quisby.formatting.add_formatting import update_conditional_formatting
from quisby.sheet.sheet_util import read_sheet, get_sheet, append_empty_row_sheet
from quisby.sheet.sheetapi import sheet
from quisby.util import read_value


def create_series_range_speccpu_process(column_count, sheetId, start_index, end_index):
    """"""
    series = []

    series.append(
        {
            "series": {
                "sourceRange": {
                    "sources": [
                        {
                            "sheetId": sheetId,
                            "startRowIndex": start_index,
                            "endRowIndex": end_index,
                            "startColumnIndex": 1,
                            "endColumnIndex": 2,
                        }
                    ]
                }
            },
            "type": "COLUMN",
        }
    )

    return series


def create_series_range_speccpu_compare(column_count, sheetId, start_index, end_index):
    series = [
        {
            "series": {
                "sourceRange": {
                    "sources": [
                        {
                            "sheetId": sheetId,
                            "startRowIndex": start_index ,
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
                            "startRowIndex": start_index ,
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
                            "startRowIndex": start_index ,
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


def graph_speccpu_data(spreadsheetId, test_name, action):
    """"""
    GRAPH_COL_INDEX = 1
    GRAPH_ROW_INDEX = 0
    start_index, end_index = None, None
    sheetId = -1
    diff_col = [3]

    data = read_sheet(spreadsheetId, test_name)
    if len(data) > 500:
        append_empty_row_sheet(spreadsheetId, 3000, test_name)

    for index, row in enumerate(data):
        if "System name" in row:
            start_index = index
            # "subtitle": f"{graph_data[0][0]}, {graph_data[0][1]}",
            title = "%s : %s" % (test_name, "Geomean")
            subtitle = "Test : %s" %(row[1].split("-")[0])
            left_title = row[1].lower()
        elif "Price-perf" in row:
            start_index = index
            test = data[start_index][0]
            title = "%s : %s" % (test_name, "Price-Performance")
            subtitle = "%s :" % (row[1].split("-")[0])
            left_title = row[1].lower()

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

            series = globals()[f'create_series_range_speccpu_{action}'](column_count, sheetId, start_index, end_index)

            requests = {
                "addChart": {
                    "chart": {
                        "spec": {
                            "title": title,
                            "subtitle": subtitle,
                            "basicChart": {
                                "chartType": "COMBO",
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
                                        "title": left_title,
                                    },
                                    {
                                        "format": {
                                            "bold": True,
                                            "italic": True,
                                            "fontSize": 14
                                        },
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
                },

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



