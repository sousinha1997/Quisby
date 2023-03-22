import logging
import time
from itertools import groupby

from pquisby.lib.sheet.sheetapi import sheet
from pquisby.lib.benchmarks.uperf.uperf import combine_uperf_data
from pquisby.lib.sheet.sheet_util import (
    append_to_sheet,
    read_sheet,
    get_sheet,
)


def series_range_uperf(column_count, sheetId, start_index, end_index):
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

def graph_uperf_data(spreadsheetId, range):
    """"""
    GRAPH_COL_INDEX, GRAPH_ROW_INDEX = 2, 0
    start_index, end_index = 0, 0
    measurement = {
        "Gb_sec": "Bandwidth",
        "trans_sec": "Transactions/second",
        "usec": "Latency",
    }
    uperf_results = read_sheet(spreadsheetId, range)
    for index, row in enumerate(uperf_results):
        if row:
            if "tcp_stream" in row[1] or "tcp_rr" in row[1] or "tcp_maerts" in row[1] or "tcp_bidirec" in row[1]:
                start_index = index

        if start_index:
            if row == []:
                end_index = index
            if index + 1 == len(uperf_results):
                end_index = index + 1

        if end_index:
            graph_data = uperf_results[start_index:end_index]
            # TODO: fix column count
            column_count = len(uperf_results[2])

            sheetId = get_sheet(spreadsheetId, range)["sheets"][0]["properties"][
                "sheetId"
            ]
            requests = {
                "addChart": {
                    "chart": {
                        "spec": {
                            "title": f"Uperf : {measurement[graph_data[0][2]]} | {graph_data[0][1]}",
                            "subtitle": f"{graph_data[0][0]}",
                            "basicChart": {
                                "chartType": "COLUMN",
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
                                "series": series_range_uperf(
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
                GRAPH_COL_INDEX = 2
            else:
                GRAPH_COL_INDEX += 6
            body = {"requests": requests}
            sheet.batchUpdate(spreadsheetId=spreadsheetId, body=body).execute()
            # Reset variables
            start_index, end_index = 0, 0
            time.sleep(1)
