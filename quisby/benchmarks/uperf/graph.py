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
    GRAPH_COL_INDEX, GRAPH_ROW_INDEX = 8, 0
    start_index, end_index = 0, 0
    diff_col = []
    sheetId = -1
    measurement = {
        "GB_Sec": "Bandwidth",
        "trans_sec": "Transactions/second",
        "usec": "Latency",
    }

    uperf_results = read_sheet(spreadsheetId, range)
    if len(uperf_results) > 500:
        append_empty_row_sheet(spreadsheetId, 3000, range)

    for index, row in enumerate(uperf_results):
        if row:
            if "Cost/Hr" in row:
                pass
            elif "Price-Perf" in row[0]:
                start_index = index
                title = f"Uperf : Price-Performance | {row[2]}"
                subtitle = f"{row[1]}"
                left_axis = row[2]
            elif "tcp_stream16" in row[1] or "tcp_rr64" in row[1] or "tcp_stream64" in row[1] or "tcp_rr16" in row[1] or "tcp_stream16384" in row[1] or "tcp_rr16384" in row[1]:
                start_index = index
                title= f"Uperf : {measurement[row[2]]} | {row[1]}"
                subtitle = ""
                left_axis = row[2]

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
                                        "title": "Instance count",
                                    },
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

            if GRAPH_COL_INDEX >= 12:
                GRAPH_ROW_INDEX += 20
                GRAPH_COL_INDEX = 8
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
