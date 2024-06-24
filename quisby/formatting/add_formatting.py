from quisby.sheet.sheetapi import sheet
from quisby import custom_logger


def update_conditional_formatting(spreadsheet_id, sheet_id, column_index, threshold):
    requests = [
        {
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [
                        {
                            "sheetId": sheet_id,
                            "startRowIndex": 0,
                            "endRowIndex": 1000,
                            "startColumnIndex": column_index,
                            "endColumnIndex": column_index + 1
                        }
                    ],
                    "booleanRule": {
                        "condition": {
                            "type": "NUMBER_LESS_THAN_EQ",
                            "values": [{"userEnteredValue": "-{}".format(threshold)}]
                        },
                        "format": {
                            "backgroundColor": {"red": 34}
                        }
                    }
                },
                "index": 0  # Set priority (optional)
            }
        }
    ]
    batch_update_body = {
        "requests": requests
    }
    sheet.batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=batch_update_body
    ).execute()


