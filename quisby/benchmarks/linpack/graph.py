import time

from quisby.formatting.add_formatting import update_conditional_formatting
from quisby.sheet.sheet_util import (
    read_sheet,
    get_sheet, append_empty_row_sheet, append_empty_col_sheet
)
from quisby.sheet.sheetapi import sheet
from quisby.util import read_value


def create_series_range_linpack(column_count, sheetId, start_index, end_index):
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


def graph_linpack_compare(spreadsheetId, test_name, action):
    """
    Re-arrange data from the sheet into a dict grouped by machine name.
    The sheet data & charts are then cleared excluding the header row.
    The function then processes loops over each groups of machine and plots the
    graphs.

    Graphs:
    - GFLOP and GFLOPS scaling
    - Price-perf

    :sheet: sheet API function
    :spreadsheetId
    :range: range to graph up the data, it will be mostly sheet name
    """
    GFLOPS_PLOT_RANGE = "B"
    PRICE_PER_PERF_RANGE = "H"
    GRAPH_COL_INDEX = 5
    start_index, end_index = None, None

    data = read_sheet(spreadsheetId, test_name)
    if len(data) > 500:
        append_empty_row_sheet(spreadsheetId, 3000, test_name)
    header_row = data[0]
    last_row = len(data)
    diff_col = [4, 7, 11]
    sheetId = -1
    GRAPH_ROW_INDEX = last_row + 1

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
            if column_count > 10:
                append_empty_col_sheet(spreadsheetId, 20, test_name)

            sheetId = get_sheet(spreadsheetId, test_name)["sheets"][0]["properties"][
                "sheetId"
            ]

            # GFlops & Diff  graph
            requests = {
                "addChart": {
                    "chart": {
                        "spec": {
                            "title": "%s : %s and %s" % (test_name, header_row[2], header_row[3]),
                            "basicChart": {
                                "chartType": "COMBO",
                                "legendPosition": "RIGHT_LEGEND",
                                "axis": [
                                    {
                                        "position": "BOTTOM_AXIS",
                                        "title": "",
                                    },
                                    {
                                        "position": "LEFT_AXIS",
                                        "title": "%s and %s"
                                                 % (
                                                     header_row[2],
                                                     header_row[3],
                                                 ),
                                    },
                                    {
                                        "position": "RIGHT_AXIS",
                                        "title": header_row[4]
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
                                                        "startColumnIndex": 4,
                                                        "endColumnIndex": 5,
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
                                    "columnIndex": 0,
                                }
                            }
                        },
                    }
                }
            }

            body = {"requests": requests}

            sheet.batchUpdate(spreadsheetId=spreadsheetId, body=body).execute()

            # Price-perf graph
            requests = {
                "addChart": {
                    "chart": {
                        "spec": {
                            "title": "%s : Price-Performance" % (test_name),
                            "basicChart": {
                                "chartType": "COMBO",
                                "legendPosition": "RIGHT_LEGEND",
                                "axis": [
                                    {
                                        "position": "BOTTOM_AXIS",
                                        "title": "Price Perf",
                                    },
                                    {
                                        "position": "LEFT_AXIS",
                                        "title": "%s and %s "
                                                 % (
                                                     header_row[9],
                                                     header_row[10],
                                                 ),
                                    },
                                    {
                                        "position": "RIGHT_AXIS",
                                        "title": header_row[11]
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
                                                        "startColumnIndex": 9,
                                                        "endColumnIndex": 10,
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
                                                        "startColumnIndex": 10,
                                                        "endColumnIndex": 11,
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
                                                        "startColumnIndex": 11,
                                                        "endColumnIndex": 12,
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
                                    "columnIndex": 6,
                                }
                            }
                        },
                    }
                }
            }

            body = {"requests": requests}

            sheet.batchUpdate(spreadsheetId=spreadsheetId, body=body).execute()

            requests = {
                "addChart": {
                    "chart": {
                        "spec": {
                            "title": "%s : GFLOP Scaling" %(test_name),
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
                                        "title": "",
                                    },
                                    {
                                        "format": {
                                            "bold": True,
                                            "italic": True,
                                            "fontSize": 14
                                        },
                                        "position": "LEFT_AXIS", "title": "GFlops Scaling "},
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
                                                        "startColumnIndex": 5,
                                                        "endColumnIndex": 6,
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
                                                        "startColumnIndex": 6,
                                                        "endColumnIndex": 7,
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
                                                        "startColumnIndex": 7,
                                                        "endColumnIndex": 8,
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
                                    "columnIndex": 12,
                                },
                                "offsetXPixels": 100,
                                "widthPixels": 600,
                                "heightPixels": 400
                            }
                        },
                    }
                }
            }

            body = {"requests": requests}

            sheet.batchUpdate(spreadsheetId=spreadsheetId, body=body).execute()

            GRAPH_ROW_INDEX += 20
            start_index, end_index = None, None

    if sheetId != -1:
        threshold = read_value("percent_threshold", test_name)
        if not threshold:
            threshold = "5"
        for col in diff_col:
            try:
                update_conditional_formatting(spreadsheetId, sheetId, col, threshold)
            except Exception as exc:
                pass


def graph_linpack_data(spreadsheetId, test_name, action):
    """
    Re-arrange data from the sheet into a dict grouped by machine name.
    The sheet data & charts are then cleared excluding the header row.
    The function then processes loops over each groups of machine and plots the
    graphs.

    Graphs:
    - GFLOP and GFLOPS scaling
    - Price-perf

    :sheet: sheet API function
    :spreadsheetId
    :test_name: test_name
    """
    if action == "compare":
        graph_linpack_compare(spreadsheetId, test_name, "compare")
        return
    GFLOPS_PLOT_RANGE = "C"
    PRICE_PER_PERF_RANGE = "E"
    GRAPH_COL_INDEX = 5
    data = read_sheet(spreadsheetId, test_name)
    last_row = len(data)
    GRAPH_ROW_INDEX = last_row + 1
    start_index, end_index = None, None
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
                            "title": "%s : %s and %s"
                                     % (test_name, header_row[2].split("-")[0], header_row[3].split("-")[0]),
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
                                        "title": "%s" % (header_row[0]),
                                    },
                                    {
                                        "format": {
                                            "bold": True,
                                            "italic": True,
                                            "fontSize": 14
                                        },
                                        "position": "LEFT_AXIS",
                                        "title": "%s and %s"
                                                 % (header_row[2].lower(), header_row[3].lower()),
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
                                    "columnIndex": 0,
                                },
                                "offsetXPixels": 100,
                                "widthPixels": 600,
                                "heightPixels": 400
                            }
                        },
                    }
                }
            }

            # Price-perf graph
            body = {"requests": requests}

            sheet.batchUpdate(spreadsheetId=spreadsheetId, body=body).execute()

            requests = {
                "addChart": {
                    "chart": {
                        "spec": {
                            "title": "%s : Price-Performance" %(test_name),
                            "basicChart": {
                                "chartType": "COLUMN",
                                "legendPosition": "RIGHT_LEGEND",
                                "axis": [
                                    {
                                        "format": {
                                            "bold": True,
                                            "italic": True,
                                            "fontSize": 14
                                        },
                                        "position": "BOTTOM_AXIS",
                                        "title": "%s" % (header_row[0]),
                                    },
                                    {
                                        "format": {
                                            "bold": True,
                                            "italic": True,
                                            "fontSize": 14
                                        },
                                        "position": "LEFT_AXIS",
                                        "title": "%s " % (header_row[5]),
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
                                                        "startColumnIndex": 5,
                                                        "endColumnIndex": 6,
                                                    }
                                                ]
                                            }
                                        },
                                        "targetAxis": "LEFT_AXIS",
                                        "type": "COLUMN",
                                    }
                                ],
                                "headerCount": 1,
                            },
                        },
                        "position": {
                            "overlayPosition": {
                                "anchorCell": {
                                    "sheetId": sheetId,
                                    "rowIndex": GRAPH_ROW_INDEX,
                                    "columnIndex": 6,
                                },
                                "offsetXPixels": 100,
                                "widthPixels": 600,
                                "heightPixels": 400
                            }
                        },
                    }
                }
            }

            body = {"requests": requests}

            sheet.batchUpdate(spreadsheetId=spreadsheetId, body=body).execute()

            GRAPH_ROW_INDEX += 20
            start_index, end_index = None, None

            time.sleep(3)


