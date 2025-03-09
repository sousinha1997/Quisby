from quisby.formatting.add_formatting import update_conditional_formatting
from quisby.sheet.sheet_util import read_sheet,clear_sheet_charts,get_sheet,append_empty_row_sheet
from quisby.sheet.sheetapi import sheet
from quisby.util import read_value
import time

# Function to create series for "coremark process" type chart
def create_series_range_list_coremark_process(column_count, sheetId, start_index, end_index):
    series = []

    # Loop through each column to create the corresponding series
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
                        ],
                    },
                },
                "type": "COLUMN", # Column type for the chart
            }
        )

    return series



# Function to create series for "coremark compare" type chart
def create_series_range_list_coremark_compare(column_count, sheetId, start_index, end_index):
    series = [
        # Series 1 for the left axis
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
            "type": "COLUMN", # Column type for the chart
        },
        # Series 2 for the left axis
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
            "type": "COLUMN",  # Column type for the chart
        },
        # Series 3 for the right axis (line chart)
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
            "type": "LINE", # Line type for the chart

        },
    ]
    return series


# Main function to create a chart based on CoreMark data
def graph_coremark_data(spreadsheetId, range, action):
    GRAPH_COL_INDEX = 1 # Initial column index for the graph
    GRAPH_ROW_INDEX = 1 # Initial row index for the graph
    start_index = 0
    end_index = 0
    diff_col = [3] # Column(s) for applying conditional formatting
    data = read_sheet(spreadsheetId, range) # Fetch data from the specified range

    # Check if data exceeds 500 rows, and append empty rows if necessary
    if len(data) > 500:
        append_empty_row_sheet(spreadsheetId, 3000, range)

    header_row = []
    sheetId = -1

    # Process the rows to find the start and end indices, and define chart title/subtitle
    for index, row in enumerate(data):
        if "System name" in row:
            start_index = index
            header_row.extend(row)
            title = "%s : %s" % (range, "Test Passes")
            subtitle = "Average Test Passes"
        elif "Price-perf" in row:
            start_index = index
            header_row.extend(row)
            title = "%s : %s" % (range, "Price-Performance")
            subtitle = "Passes/$"

        # Determine the end index based on an empty row or end of data
        if start_index:
            if not row:
                end_index = index
            if index + 1 == len(data):
                end_index = index + 1

        # Create the chart only if end_index is set
        if end_index:
            graph_data = data[start_index:end_index] # Slice the data for charting
            column_count = len(graph_data[0]) # Get the number of columns for the chart

            # Get the sheetId for the current range
            sheetId = get_sheet(spreadsheetId, range)["sheets"][0]["properties"][
                "sheetId"
            ]

            # Dynamically call the appropriate function to create series based on the action
            series = globals()[f'create_series_range_list_coremark_{action}'](column_count, sheetId, start_index, end_index)

            # Define the chart request body
            requests = {
                "addChart": {
                    "chart": {
                        "spec": {
                            "title": title,
                            "subtitle": subtitle + " : ",
                            "basicChart": {
                                "chartType": "COMBO", # Combo chart type (both column and line)
                                "legendPosition": "RIGHT_LEGEND",
                                "axis": [
                                    {
                                        "format": {
                                            "bold": True,
                                            "italic": True,
                                            "fontSize": 14
                                        },
                                        "position": "BOTTOM_AXIS",
                                        "title": "System"},
                                    {
                                        "format": {
                                            "bold": True,
                                            "italic": True,
                                            "fontSize": 14
                                        },
                                        "position": "LEFT_AXIS",
                                        "title": graph_data[0][1].split("-")[0],
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
                                    "columnIndex": column_count + GRAPH_COL_INDEX,
                                },
                                "offsetXPixels": 100,
                                "widthPixels": 600,
                                "heightPixels": 400
                            }
                        },
                    }
                }
            }

            # Adjust position if necessary
            if GRAPH_COL_INDEX >= 5:
                GRAPH_ROW_INDEX += 20
                GRAPH_COL_INDEX = 1
            else:
                GRAPH_COL_INDEX += 6

            # Execute the batch update to create the chart
            body = {"requests": requests}

            sheet.batchUpdate(spreadsheetId=spreadsheetId, body=body).execute()

            # Reset start and end indices for the next graph
            start_index, end_index = 0, 0

            time.sleep(3)


    # Apply conditional formatting if sheetId is valid
    if sheetId != -1:
        threshold = read_value("percent_threshold", range)
        if not threshold:
            threshold = "5" # Default threshold value
        for col in diff_col:
            update_conditional_formatting(spreadsheetId, sheetId, col, threshold)


