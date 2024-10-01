import time

from quisby.formatting.add_formatting import update_conditional_formatting
from quisby.sheet.sheet_util import read_sheet, get_sheet, append_empty_row_sheet
from quisby.sheet.sheetapi import sheet
from quisby.util import read_value


def create_series_range_list_pyperf_process(column_count, sheetId, start_index, end_index):
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


def create_series_range_list_pyperf_compare(column_count, sheetId, start_index, end_index):
    series = [
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
            "targetAxis": "LEFT_AXIS",
            "type": "COLUMN",
        },
        {
            "series": {
                "sourceRange": {
                    "sources": [
                        {
                            "sheetId": sheetId,
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
                            "sheetId": sheetId,
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


def graph_pyperf_data(spreadsheetId, range, action):
    GRAPH_COL_INDEX = 1
    GRAPH_ROW_INDEX = 1
    start_index = 0
    end_index = 0
    sheetId = -1
    diff_col = [3]
    row_val = 1

    data = read_sheet(spreadsheetId, range)
    if len(data) > 500:
        append_empty_row_sheet(spreadsheetId, 3000, range)

    for index, row in enumerate(data):
        for col in row:
            if "System name" in col:
                start_index = index
                if row_val == 1:
                    row_val = start_index
                title = "%s : %s" % (range, "Geomean")
                subtitle = ""
            elif "Price-perf" in row:
                start_index = index
                if row_val == 1:
                    row_val = start_index
                title = "%s : %s" % (range, "Price-Performance")
                subtitle = "Geomean/$"
        if start_index:
            if not row:
                end_index = index
            if index + 1 == len(data):
                end_index = index + 1

        if end_index:

            graph_data = data[start_index:end_index]
            column_count = len(graph_data[0])

            sheetId = get_sheet(spreadsheetId, range)["sheets"][0]["properties"][
                "sheetId"
            ]

            series = globals()[f'create_series_range_list_pyperf_{action}'](column_count, sheetId, start_index, end_index)

            requests = {
                "addChart": {
                    "chart": {
                        "spec": {
                            "title": title,
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
                                        "title":  graph_data[0][1].split("-")[0].lower(),
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
                                    "rowIndex": GRAPH_ROW_INDEX ,
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

            # Reset variables
            start_index, end_index = 0, 0

            time.sleep(3)
    if sheetId != -1:
        threshold = read_value("percent_threshold", range)
        if not threshold:
            threshold = "5"
        for col in diff_col:
            update_conditional_formatting(spreadsheetId, sheetId, col, threshold)