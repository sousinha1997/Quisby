from itertools import groupby
import time
from quisby.sheet.sheetapi import sheet
from quisby.sheet.sheet_util import (
    clear_sheet_charts,
    clear_sheet_data,
    append_to_sheet,
    read_sheet,
    get_sheet,append_empty_row_sheet
)


def series_range_hammerdb_process(column_count, sheetId, start_index, end_index):
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


def series_range_hammerdb_compare(column_count, sheetId, start_index, end_index):
    series = []
    column_index = 1
    while column_index < column_count:
        series.extend([
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
            },
            {
                "series": {
                    "sourceRange": {
                        "sources": [
                            {
                                "sheetId": sheetId,
                                "startRowIndex": start_index,
                                "endRowIndex": end_index,
                                "startColumnIndex": column_index + 1,
                                "endColumnIndex": column_index + 2,
                            }
                        ]
                    }
                },
                "targetAxis": "LEFT_AXIS",
                "type": "COLUMN",
            },
        ])
        column_index = column_index + 3

    return series


def graph_hammerdb_data(spreadsheetId, range, action):
    """"""

    hammerdb_results = read_sheet(spreadsheetId, range)
    LAST_ROW = len(hammerdb_results)

    GRAPH_COL_INDEX, GRAPH_ROW_INDEX = 0, LAST_ROW+1
    start_index, end_index = 0, 0
    if len(hammerdb_results) > 500:
        append_empty_row_sheet(spreadsheetId, 3000, range)

    for index, row in enumerate(hammerdb_results):

        if row:
            if "User Count" in row[0]:
                header_name = row[0].split("-")[0]
                start_index = index

        if start_index:
            if not row:
                end_index = index
            if index + 1 == len(hammerdb_results):
                end_index = index + 1

        if end_index:
            graph_data = hammerdb_results[start_index:end_index]
            column_count = len(graph_data[0])

            sheetId = get_sheet(spreadsheetId, range)["sheets"][0]["properties"][
                "sheetId"
            ]

            requests = {
                "addChart": {
                    "chart": {
                        "spec": {
                            "title": f"{header_name}",
                            "basicChart": {
                                "chartType": "COMBO",
                                "legendPosition": "BOTTOM_LEGEND",
                                "axis": [
                                    {
                                        "position": "BOTTOM_AXIS",
                                        "title": "User count",
                                    },
                                    {
                                        "position": "LEFT_AXIS",
                                        "title": f"TPMs",
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
                                "series": globals()[f'series_range_hammerdb_{action}'](
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
                                    "columnIndex": GRAPH_COL_INDEX,
                                }
                            }
                        },
                    }
                }
            }

            if GRAPH_COL_INDEX >= 10:
                GRAPH_ROW_INDEX += 20
                GRAPH_COL_INDEX = 0
            else:
                GRAPH_COL_INDEX += 6

            body = {"requests": requests}

            sheet.batchUpdate(spreadsheetId=spreadsheetId, body=body).execute()

            # Reset variables
            start_index, end_index = 0, 0
            time.sleep(3)
