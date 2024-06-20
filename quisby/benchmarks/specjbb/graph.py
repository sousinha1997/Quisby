import time

from quisby import custom_logger
from quisby.formatting.add_formatting import update_conditional_formatting
from quisby.sheet.sheet_util import (
    read_sheet,
    get_sheet, append_empty_row_sheet
)
from quisby.sheet.sheetapi import sheet


def create_series_range_list_specjbb_process(column_count, sheetId, start_index, end_index):
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


def create_series_range_list_specjbb_compare(column_count, sheetId, start_index, end_index):
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


def graph_specjbb_data(spreadsheetId, range, action):
    GRAPH_COL_INDEX = 1
    GRAPH_ROW_INDEX = 0
    start_index = 0
    end_index = 0
    sheetId = -1
    diff_col = [3]

    data = read_sheet(spreadsheetId, range)
    if len(data) > 500:
        append_empty_row_sheet(spreadsheetId, 3000, range)

    for index, row in enumerate(data):
        try:
            if "Peak" in row or "Peak/$eff" in row:
                start_index = index

            if start_index:
                if row == []:
                    end_index = index
                if index + 1 == len(data):
                    end_index = index + 1

            if end_index:
                graph_data = data[start_index:end_index]
                column_count = len(graph_data[0])

                sheetId = get_sheet(spreadsheetId, range)["sheets"][0]["properties"][
                    "sheetId"
                ]

                requests = {
                    "addChart": {
                        "chart": {
                            "spec": {
                                "title": "%s : %s" % (range, graph_data[0][0]),
                                "basicChart": {
                                    "chartType": "COMBO",
                                    "legendPosition": "BOTTOM_LEGEND",
                                    "axis": [
                                        {"position": "BOTTOM_AXIS", "title": ""},
                                        {
                                            "position": "LEFT_AXIS",
                                            "title": "Throughput(bops)",
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
                                    "series": globals()[f'create_series_range_list_specjbb_{action}'](
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

                # Reset variables
                start_index, end_index = 0, 0

                time.sleep(3)
        except Exception as exc:
            custom_logger.debug(str(exc))
            custom_logger.error("Unable to graph specjbb data")

    if sheetId != -1:
        for col in diff_col:
            update_conditional_formatting(spreadsheetId, sheetId, col)