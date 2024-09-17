import time
from itertools import groupby

from quisby.formatting.add_formatting import update_conditional_formatting
from quisby.sheet.sheet_util import (
    read_sheet,
    get_sheet, append_empty_row_sheet
)
from quisby.sheet.sheetapi import sheet
from quisby.util import read_value


def create_series_range_list_stream_compare(column_index, len_of_func, sheetId, start_index, end_index):
    series = []
    len_of_func = column_index + len_of_func
    diff_col = []
    while column_index < len_of_func:
        series.append(
            {
                "series": {
                    "sourceRange": {
                        "sources": [
                            {
                                "sheetId": sheetId,
                                "startRowIndex": start_index,
                                "endRowIndex": end_index,
                                "startColumnIndex": column_index,
                                "endColumnIndex": column_index + 1,
                            }
                        ]
                    }
                },
                "targetAxis": "LEFT_AXIS",
                "type": "COLUMN",
            }, )
        column_index = column_index + 1

    series.append({
        "series": {
            "sourceRange": {
                "sources": [
                    {
                        "sheetId": sheetId,
                        "startRowIndex": start_index,
                        "endRowIndex": end_index,
                        "startColumnIndex": column_index,
                        "endColumnIndex": column_index + 1,
                    }
                ]
            }
        },
        "targetAxis": "RIGHT_AXIS",
        "type": "LINE",
    }, )
    diff_col.append(column_index)
    column_index = column_index + 1

    return series, column_index, diff_col


def create_series_range_list_stream_process(column_index, len_of_func, sheetId, start_index, end_index):
    series = []

    for index in range(len_of_func):
        series.append(
            {
                "series": {
                    "sourceRange": {
                        "sources": [
                            {
                                "sheetId": sheetId,
                                "startRowIndex": start_index,
                                "endRowIndex": end_index,
                                "startColumnIndex": column_index,
                                "endColumnIndex": column_index + 1,
                            }
                        ]
                    }
                },
                "type": "COLUMN",
            }
        )
        column_index += 1

    return series, column_index, []


def graph_streams_data(spreadsheetId, test_name, action):
    """
    Retreive each streams results and graph them up indvidually

    :sheet: sheet API function
    :spreadsheetId
    :test_name: test_name to graph up the data, it will be mostly sheet name
    """

    start_index = 0
    end_index = 0
    sheetId = -1
    diff_col = []
    data = read_sheet(spreadsheetId, "streams")
    last_row = len(data)
    GRAPH_COL_INDEX, GRAPH_ROW_INDEX = 0, last_row + 1

    if len(data) > 500:
        append_empty_row_sheet(spreadsheetId, 3000, test_name)
    if len(data) > 1000:
        append_empty_row_sheet(spreadsheetId, 1000, test_name)
    for index, row in enumerate(data):
        if "Max Throughput" in row:
            start_index = index
            title = "%s: %s" % (test_name, "Max Throughput")
            left_axis = "Throughput( MB/s )"

        if "Price-Perf" in row:
            start_index = index
            title = "%s: %s" % (test_name, "Price-Performance")
            left_axis = "Throughput/$"

        if start_index:
            if row == []:
                end_index = index
            if index + 1 == len(data):
                end_index = index + 1

        if end_index:
            graph_data = data[start_index:end_index]
            column_count = len(graph_data[0])

            for _, items in groupby(graph_data[0][1:], key=lambda x: x.split("-")[0]):
                len_of_func = len(list(items))
                break
            column = 1

            for _ in range(column_count):
                if column >= column_count:
                    break

                sheetId = get_sheet(spreadsheetId, test_name)["sheets"][0][
                    "properties"
                ]["sheetId"]

                series, column,col = globals()[f'create_series_range_list_stream_{action}'](column, len_of_func, sheetId,
                                                                                        start_index, end_index)
                diff_col.extend(col)

                requests = {
                    "addChart": {
                        "chart": {
                            "spec": {
                                "title": title,
                                "basicChart": {
                                    "chartType": "COMBO",
                                    "legendPosition": "RIGHT_LEGEND",
                                    "axis": [
                                        {"format": {
                                            "bold": True,
                                            "italic": True,
                                            "fontSize": 14
                                        },
                                            "position": "BOTTOM_AXIS", "title": "System"},
                                        {
                                            "format": {
                                            "bold": True,
                                            "italic": True,
                                            "fontSize": 14
                                        },
                                            "position": "LEFT_AXIS",
                                            "title": left_axis,
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
                                        "columnIndex": GRAPH_COL_INDEX,
                                    },
                                "offsetXPixels": 100,
                                "widthPixels": 600,
                                "heightPixels": 400
                                }
                            },
                        }
                    }
                }

                if GRAPH_COL_INDEX >= 6:
                    GRAPH_ROW_INDEX += 20
                    GRAPH_COL_INDEX = 0
                else:
                    GRAPH_COL_INDEX += 6

                body = {"requests": requests}

                sheet.batchUpdate(spreadsheetId=spreadsheetId, body=body).execute()

                time.sleep(3)

            # Reset variables
            start_index, end_index = 0, 0

    if sheetId != -1:
        threshold = read_value("percent_threshold", test_name)
        if not threshold:
            threshold = "5"
        for col in set(diff_col):
            try:
                update_conditional_formatting(spreadsheetId, sheetId, col, threshold)
            except Exception as exc:
                print(str(exc))
                pass
