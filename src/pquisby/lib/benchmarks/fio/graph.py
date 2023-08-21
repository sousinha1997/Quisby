import time
import logging

from pquisby.lib.sheet.sheetapi import sheet
from pquisby.lib.sheet.sheet_util import (
    read_sheet,
    clear_sheet_charts,
    get_sheet,
    append_empty_row_sheet,
)


def create_series_range_fio(column_count, sheetId, start_index, end_index):
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


def graph_fio_run_data(spreadsheetId, test_name):
    GRAPH_COL_INDEX = 5
    GRAPH_ROW_INDEX = 1
    start_index, end_index = None, None

    data = read_sheet(spreadsheetId, test_name)

    if len(data) > 1000:
        append_empty_row_sheet(spreadsheetId, 500, test_name)

    for index, row in enumerate(data):
        if "iteration_name" in row:
            start_index = index - 1
            continue

        if start_index:
            if index + 1 == len(data):
                end_index = index + 1
            elif row == []:
                end_index = index

        if end_index:
            logging.info(
                f"Creating graph for table index {start_index}-{end_index} in sheet"
            )
            try:
                graph_data = data[start_index:end_index]

                column_count = len(graph_data[2])
            except IndexError:
                logging.error(f"{test_name}: Data inconsistency at {start_index}-{end_index}. Skipping to next data")
                continue

            sheetId = get_sheet(spreadsheetId, test_name)["sheets"][0]["properties"][
                "sheetId"
            ]

            requests = {
                "addChart": {
                    "chart": {
                        "spec": {
                            "title": f"{graph_data[0][2].split('-')[1]}:{graph_data[0][1]} {graph_data[0][2].split('-')[0]}",
                            "subtitle": f"{graph_data[0][0]} | d:Disks, j:Jobs, iod:IODepth",
                            "basicChart": {
                                "chartType": "COLUMN",
                                "axis": [
                                    {
                                        "position": "LEFT_AXIS",
                                        "title": "Mb/sec",
                                    },
                                ],
                                "domains": [
                                    {
                                        "domain": {
                                            "sourceRange": {
                                                "sources": [
                                                    {
                                                        "sheetId": sheetId,
                                                        "startRowIndex": start_index + 1,
                                                        "endRowIndex": end_index + 1,
                                                        "startColumnIndex": 0,
                                                        "endColumnIndex": 1,
                                                    }
                                                ]
                                            }
                                        }
                                    }
                                ],
                                "series": create_series_range_fio(
                                    column_count, sheetId, start_index, end_index + 1
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
            if GRAPH_COL_INDEX >= 6:
                GRAPH_ROW_INDEX += 18
                GRAPH_COL_INDEX = 5
            else:
                GRAPH_COL_INDEX += 6

            body = {"requests": requests}

            sheet.batchUpdate(spreadsheetId=spreadsheetId, body=body).execute()

            start_index, end_index = None, None
            logging.info("Sleep for 1sec to workaround Gsheet API")

            time.sleep(1)

