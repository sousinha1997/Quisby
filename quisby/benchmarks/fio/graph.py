import time

from quisby import custom_logger
from quisby.formatting.add_formatting import update_conditional_formatting
from quisby.sheet.sheet_util import (
    read_sheet,
    get_sheet,
    append_empty_row_sheet,
)
from quisby.sheet.sheetapi import sheet
from quisby.util import read_value


def create_series_range_fio_process(column_count, sheetId, start_index, end_index, graph):
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


def create_series_range_fio_compare(column_count, sheetId, start_index, end_index, graph):
    series = [
        {
            "series": {
                "sourceRange": {
                    "sources": [
                        {
                            "sheetId": sheetId,
                            "startRowIndex": start_index + 1,
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
                            "startRowIndex": start_index + 1,
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
        # {
        #     "series": {
        #         "sourceRange": {
        #             "sources": [
        #                 {
        #                     "sheetId": sheetId,
        #                     "startRowIndex": start_index + 1,
        #                     "endRowIndex": end_index,
        #                     "startColumnIndex": 3,
        #                     "endColumnIndex": 4,
        #                 }
        #             ]
        #         }
        #     },
        #     "targetAxis": "RIGHT_AXIS",
        #     "type": graph,
        # },
    ]
    return series


def graph_fio_run_data(spreadsheetId, test_name, action):
    GRAPH_COL_INDEX = 5
    GRAPH_ROW_INDEX = 1
    start_index, end_index = None, None
    measurement = {
        "iops": "Mb/sec",
        "lat": "secs",
    }
    left_axis = ""
    diff_col = [3]
    sheetId = -1

    data = read_sheet(spreadsheetId, test_name)

    if len(data) > 500:
        append_empty_row_sheet(spreadsheetId, 3000, test_name)

    for index, row in enumerate(data):
        if "iteration_name" in row:
            start_index = index - 1
            test_det = row[1]
            left_axis = ""
            for key in measurement:
                if key in test_det:
                    left_axis = measurement.get(key)
                    break
            continue

        if start_index:
            if index + 1 == len(data):
                end_index = index + 1
            elif row == []:
                end_index = index

        if end_index:
            if end_index - start_index == 3:
                graph = "COLUMN"
            else:
                graph = "LINE"
            custom_logger.info(
                f"Creating graph for table index {start_index}-{end_index} in sheet"
            )
            try:
                graph_data = data[start_index:end_index]
                column_count = len(graph_data[2])

            except IndexError:
                custom_logger.error(
                    f"{test_name}: Data inconsistency at {start_index}-{end_index}. Skipping to next data")
                continue

            sheetId = get_sheet(spreadsheetId, test_name)["sheets"][0]["properties"][
                "sheetId"
            ]

            series = globals()[f'create_series_range_fio_{action}'](column_count, sheetId, start_index, end_index + 1, graph)

            requests = {
                "addChart": {
                    "chart": {
                        "spec": {
                            "title": f"{graph_data[0][2].split('-')[1]}:{graph_data[0][1]} {graph_data[0][2].split('-')[0]}",
                            "subtitle": f"{graph_data[0][0]} | d:Disks, j:Jobs, iod:IODepth",
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
                                    {
                                        "format": {
                                            "bold": True,
                                            "italic": True,
                                            "fontSize": 14
                                        },
                                        "position": "BOTTOM_AXIS",
                                        "title": "System",
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
            if GRAPH_COL_INDEX >= 16:
                GRAPH_ROW_INDEX += 20
                GRAPH_COL_INDEX = 5
            else:
                GRAPH_COL_INDEX += 6

            body = {"requests": requests}

            sheet.batchUpdate(spreadsheetId=spreadsheetId, body=body).execute()

            start_index, end_index = None, None
            custom_logger.info("Sleep for 1sec to workaround Gsheet API")

            time.sleep(3)

    if sheetId != -1:
        threshold = read_value("percent_threshold", test_name)
        if not threshold:
            threshold = "5"
        for col in diff_col:
            update_conditional_formatting(spreadsheetId, sheetId, col, threshold)
