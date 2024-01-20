from quisby import custom_logger

from quisby.sheet.sheetapi import sheet
from quisby.sheet.sheet_util import (
    read_sheet,
    append_to_sheet,
    clear_sheet_charts,
    clear_sheet_data,
    get_sheet,
    create_sheet,
)


def graph_linpack_comparison(spreadsheetId, test_name):
    """
    Re-arrange data from the sheet into a dict grouped by machine name.
    The sheet data & charts are then cleared excluding the header row.
    The function then processes loops over each groups of machine and plots the
    graphs.

    Graphs:
    - GFLOP and GFLOPS scaling
    - Price/perf

    :sheet: sheet API function
    :spreadsheetId
    :range: range to graph up the data, it will be mostly sheet name
    """
    GFLOPS_PLOT_RANGE = "B"
    PRICE_PER_PERF_RANGE = "H"
    GRAPH_COL_INDEX = 5
    GRAPH_ROW_INDEX = 0
    start_index, end_index = None, None

    data = read_sheet(spreadsheetId, test_name)
    header_row = data[0]

    for index, row in enumerate(data):
        if row[0] == "System" and start_index is None:
            start_index = index
            continue

        if start_index is not None:
            if index + 1 == len(data):
                end_index = index + 1
            elif data[index + 1][0] == "System":
                end_index = index + 1

        if end_index:
            graph_data = data[start_index:end_index]
            column_count = len(graph_data[0])

            sheetId = get_sheet(spreadsheetId, test_name)["sheets"][0]["properties"][
                "sheetId"
            ]

            # GFlops & GFlops scaling graph
            requests = {
                "addChart": {
                    "chart": {
                        "spec": {
                            "title": "%s and %s" % (header_row[2], header_row[3]),
                            "basicChart": {
                                "chartType": "COMBO",
                                "legendPosition": "BOTTOM_LEGEND",
                                "axis": [
                                    {
                                        "position": "BOTTOM_AXIS",
                                        "title": "",
                                    },
                                    {
                                        "position": "LEFT_AXIS",
                                        "title": "%s, %s and %s, %s "
                                        % (
                                            header_row[2],
                                            header_row[3],
                                            header_row[5],
                                            header_row[6],
                                        ),
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
                                "series": [
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
                                                        "startColumnIndex": 5,
                                                        "endColumnIndex": 6,
                                                    }
                                                ]
                                            }
                                        },
                                        "targetAxis": "RIGHT_AXIS",
                                        "type": "LINE",
                                    },
                                    {
                                        "series": {
                                            "sourceRange": {
                                                "sources": [
                                                    {
                                                        "sheetId": sheetId,
                                                        "startRowIndex": start_index,
                                                        "endRowIndex": end_index,
                                                        "startColumnIndex": 6,
                                                        "endColumnIndex": 7,
                                                    }
                                                ]
                                            }
                                        },
                                        "targetAxis": "RIGHT_AXIS",
                                        "type": "LINE",
                                    },
                                ],
                                "headerCount": 1,
                            },
                        },
                        "position": {
                            "overlayPosition": {
                                "anchorCell": {
                                    "sheetId": sheetId,
                                    "rowIndex": GRAPH_ROW_INDEX,
                                    "columnIndex": column_count + 1,
                                }
                            }
                        },
                    }
                }
            }

            # PRICE/PERF graph
            body = {"requests": requests}

            sheet.batchUpdate(spreadsheetId=spreadsheetId, body=body).execute()

            requests = {
                "addChart": {
                    "chart": {
                        "spec": {
                            "title": "Price/Perf ",
                            "basicChart": {
                                "chartType": "COLUMN",
                                "legendPosition": "BOTTOM_LEGEND",
                                "axis": [
                                    {
                                        "position": "BOTTOM_AXIS",
                                        "title": "",
                                    },
                                    {"position": "LEFT_AXIS", "title": "GFlops/$/hr "},
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
                                "series": [
                                    {
                                        "series": {
                                            "sourceRange": {
                                                "sources": [
                                                    {
                                                        "sheetId": sheetId,
                                                        "startRowIndex": start_index,
                                                        "endRowIndex": end_index,
                                                        "startColumnIndex": 8,
                                                        "endColumnIndex": 9,
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
                                                        "startColumnIndex": 9,
                                                        "endColumnIndex": 10,
                                                    }
                                                ]
                                            }
                                        },
                                        "targetAxis": "LEFT_AXIS",
                                        "type": "COLUMN",
                                    },
                                ],
                                "headerCount": 1,
                            },
                        },
                        "position": {
                            "overlayPosition": {
                                "anchorCell": {
                                    "sheetId": sheetId,
                                    "rowIndex": GRAPH_ROW_INDEX,
                                    "columnIndex": column_count + 7,
                                }
                            }
                        },
                    }
                }
            }

            body = {"requests": requests}

            sheet.batchUpdate(spreadsheetId=spreadsheetId, body=body).execute()

            GRAPH_ROW_INDEX += 20
            start_index, end_index = None, None

def percent_deviation(item1,item2):
    item1 = float(item1)
    item2 = float(item2)
    if (item1 == 0.0 == item2):
        percentage_deviation = 0.0
    elif (item1 == 0.0):
        percentage_deviation = item2
    elif (item2 == 0.0):
        percentage_deviation = 0.0-item1
    else:
        percentage_deviation = ((item2 - item1) / item1) * 100
    return percentage_deviation

def compare_linpack_results(spreadsheets, spreadsheetId, test_name):
    values = []
    results = []
    spreadsheet_name = []

    for spreadsheet in spreadsheets:
        values.append(read_sheet(spreadsheet, test_name))
        spreadsheet_name.append(
            get_sheet(spreadsheet, test_name)["properties"]["title"]
        )

    for value in values[0]:
        for ele in values[1]:
            if value[0] == "System" and ele[0] == "System":
                results.append(
                    [
                        value[0],
                        value[1],
                        value[2],
                        ele[2],
                        "% Diff",
                        value[3],
                        ele[3],
                        value[4],
                        value[5],
                        ele[5],
                        "Price/Perf % Diff",
                    ]
                )
                break
            else:
                if value[0] == ele[0]:
                    price_perf = []

                    price_perf.append(float(value[2]) / float(value[4]))
                    price_perf.append(float(ele[2]) / float(ele[4]))
                    price_perf_diff = percent_deviation(price_perf[0], price_perf[1])
                    # price_perf_diff = (
                    #     float(price_perf[1]) - float(price_perf[0])
                    # ) / float(price_perf[0])
                    percentage_diff = percent_deviation(value[2], ele[2])
                    # percentage_diff = (float(ele[2]) - float(value[2])) / float(
                    #     value[2]
                    # )

                    results.append(
                        [
                            value[0],
                            value[1],
                            value[2],
                            ele[2],
                            percentage_diff,
                            value[3],
                            ele[3],
                            value[4],
                            price_perf[0],
                            price_perf[1],
                            price_perf_diff,
                        ]
                    )
    try:
        create_sheet(spreadsheetId, test_name)
        custom_logger.info("Deleting existing charts and data from the sheet...")
        clear_sheet_charts(spreadsheetId, test_name)
        clear_sheet_data(spreadsheetId, test_name)
        custom_logger.info("Appending new " + test_name + " data to sheet...")
        append_to_sheet(spreadsheetId, results, test_name)
        graph_linpack_comparison(spreadsheetId, test_name)
    except Exception as exc:
        custom_logger.debug(str(exc))
        custom_logger.error("Failed to append data to sheet")
        return spreadsheetId

