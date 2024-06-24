import time

from quisby.formatting.add_formatting import update_conditional_formatting
from quisby.sheet.sheet_util import (
    read_sheet,
    get_sheet, append_empty_row_sheet, append_empty_col_sheet
)
from quisby.sheet.sheetapi import sheet
from quisby.util import read_value


def series_range_uperf_process(column_count, sheetId, start_index, end_index):
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

    return series,[]


def series_range_uperf_compare(column_count, sheetId, start_index, end_index):
    series = []
    diff_col = []
    for index in range(1, column_count, 3):
        diff_col.append(index+2)
        series.append({
            "series": {
                "sourceRange": {
                    "sources": [
                        {
                            "sheetId": sheetId,
                            "startRowIndex": start_index + 1,
                            "endRowIndex": end_index,
                            "startColumnIndex": index,
                            "endColumnIndex": index + 1,
                        }
                    ]
                }
            },
            "targetAxis": "LEFT_AXIS",
            "type": "COLUMN",
        })
        series.append({
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
            "targetAxis": "LEFT_AXIS",
            "type": "COLUMN",
        })
        # series.append({
        #         "series": {
        #             "sourceRange": {
        #                 "sources": [
        #                     {
        #                         "sheetId": sheetId,
        #                         "startRowIndex": start_index + 1,
        #                         "endRowIndex": end_index,
        #                         "startColumnIndex": index + 2,
        #                         "endColumnIndex": index + 3,
        #                     }
        #                 ]
        #             }
        #         },
        #         "targetAxis": "RIGHT_AXIS",
        #         "type": "COLUMN",
        #     })

    return series, diff_col


def graph_uperf_data(spreadsheetId, range, action):
    """"""
    GRAPH_COL_INDEX, GRAPH_ROW_INDEX = 2, 0
    start_index, end_index = 0, 0
    diff_col = []
    sheetId = -1
    measurement = {
        "Gb_sec": "Bandwidth",
        "trans_sec": "Transactions/second",
        "usec": "Latency",
    }

    uperf_results = read_sheet(spreadsheetId, range)
    if len(uperf_results) > 500:
        append_empty_row_sheet(spreadsheetId, 3000, range)


    for index, row in enumerate(uperf_results):
        if row:
            if "tcp_stream16" in row[1] or "tcp_rr64" in row[1] or "tcp_stream64" in row[1] or "tcp_rr16" in row[1]:
                start_index = index

        if start_index:
            if not row:
                end_index = index
            if index + 1 == len(uperf_results):
                end_index = index + 1

        if end_index:
            graph_data = uperf_results[start_index:end_index]
            # TODO: fix column count
            column_count = len(graph_data[2])
            if column_count > 10:
                append_empty_col_sheet(spreadsheetId, 20, range)

            sheetId = get_sheet(spreadsheetId, range)["sheets"][0]["properties"][
                "sheetId"
            ]
            series, col = globals()[f'series_range_uperf_{action}'](column_count, sheetId, start_index, end_index)
            diff_col.extend(col)
            requests = {
                "addChart": {
                    "chart": {
                        "spec": {
                            "title": f"Uperf : {measurement[graph_data[0][2]]} | {graph_data[0][1]}",
                            "subtitle": f"{graph_data[0][0]}",
                            "basicChart": {
                                "chartType": "COMBO",
                                "legendPosition": "BOTTOM_LEGEND",
                                "axis": [
                                    {
                                        "position": "BOTTOM_AXIS",
                                        "title": "Instance count",
                                    },
                                    {
                                        "position": "LEFT_AXIS",
                                        "title": f"{graph_data[0][2]}",
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
                GRAPH_COL_INDEX = 2
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
        for col in set(diff_col):
            try:
                update_conditional_formatting(spreadsheetId, sheetId, col, threshold)
            except Exception as exc:
                print(str(exc))
                pass
