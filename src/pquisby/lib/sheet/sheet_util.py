import logging
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pquisby.lib.sheet.sheetapi import creds,sheet,file
from pquisby.lib.util import write_config


def check_sheet_exists(sheet_info, test_name):
    """"""
    for sheet_prop in sheet_info:
        if test_name == sheet_prop["properties"]["title"]:
            return True
    return False

def permit_users(spreadsheetId):
    drive_api = build('drive', 'v3', credentials=creds)
    permission = {
        'type': 'anyone',
        'role': 'writer',
        'withLink': True
    }
    req = drive_api.permissions().create(
        fileId=spreadsheetId,
        body=permission,
        fields="id"
    )

    req.execute()

def create_spreadsheet(spreadsheet_name, test_name):
    """
    A new sheet is created if spreadsheetId is None

    :sheet: Google sheet API function
    :name: Spreadsheet title
    """
    spreadsheet = {
        "properties": {"title": spreadsheet_name},
        "sheets": {
            "properties": {
                "sheetId": 0,
                "title": test_name,
                "gridProperties": {
                    "frozenRowCount": 1,
                },
            }
        },
    }
    spreadsheet = sheet.create(body=spreadsheet).execute()
    spreadsheetId = spreadsheet["spreadsheetId"]
    permit_users(spreadsheetId)
    return spreadsheetId

def get_sheet(spreadsheetId, test_name,range="!a:z"):

    if test_name == []:
        #create sheet
        return sheet.get(spreadsheetId=spreadsheetId).execute()
    else:
        return sheet.get(spreadsheetId=spreadsheetId,ranges=test_name+range).execute()

def get_sheet_id(spreadsheetId, sheet_title):
    try:
        # Get the spreadsheet information
        spreadsheet = get_sheet(spreadsheetId,[])
        # Find the sheet with the specified title
        sheet = next(s for s in spreadsheet['sheets']if s['properties']['title'] == sheet_title)
        # Get the sheet ID
        sheet_id = sheet['properties']['sheetId']
        return sheet_id
    except HttpError as error:
        print(f'An error occurred: {error}')
    return None

def delete_sheet_content(spreadsheet_id,sheet_title):
    try:
        response = sheet.values().clear(spreadsheetId = spreadsheet_id,range = sheet_title).execute()
    except Exception:
        logging.warning("Unable to clear chart, might get repetitive data")
def delete_spreadsheet(spreadsheet_id):
    try:
        file.delete(fileId = spreadsheet_id).execute()
    except Exception as exc:
        logging.error("Unable to delete sheet")

def clear_sheet_charts(spreadsheetId, range="A2:Z1000"):
    # Clear charts
    sheet_properties = get_sheet(spreadsheetId, range)

    if "charts" in sheet_properties["sheets"][0]:
        for chart in sheet_properties["sheets"][0]["charts"]:

            requests = {"deleteEmbeddedObject": {"objectId": chart["chartId"]}}

            body = {"requests": requests}

            sheet.batchUpdate(spreadsheetId=spreadsheetId, body=body).execute()

def create_sheet(spreadsheetId, test_name):
    """
    New sheet in spreadsheet is created

    :sheet: Google sheet API function
    :spreadsheetId
    :test_name: range to graph up the data, it will be mostly sheet name
    """
    sheet_info = get_sheet(spreadsheetId, [])["sheets"]
    # Create sheet if it doesn't exit
    if not check_sheet_exists(sheet_info, test_name):
        sheet_count = len(sheet_info)
        requests = {
            "addSheet": {
                "properties": {
                    "sheetId": sheet_count + 1,
                    "title": test_name,
                    "gridProperties": {
                        "frozenRowCount": 1,
                    },
                }
            }
        }
        body = {"requests": requests}
        sheet.batchUpdate(spreadsheetId=spreadsheetId, body=body).execute()

def read_sheet(spreadsheet_Id, range="A:Z"):
    # TODO : check for the previous api
    request=sheet.values().batchGet(spreadsheetId=spreadsheet_Id, ranges=range)
    result=request.execute()
    values = result.get("valueRanges", [])[0].get('values',[])
    return values

def append_to_sheet(spreadsheet_Id, results, range="A:F"):
    """"""
    body = {"values": results}
    response = (
        sheet.values()
        .append(
            spreadsheetId=spreadsheet_Id,
            range=range,
            valueInputOption="USER_ENTERED",
            body=body,
        )
        .execute()
    )
    return response

def apply_named_range(spreadsheetId, name, range="A:Z"):

    sheetId = get_sheet(spreadsheetId, range)["sheets"][0]["properties"]["sheetId"]

    sheet_range = range.split("!")[1].split(":")

    body = {
        "requests": [
            {
                "addNamedRange": {
                    "namedRange": {
                        "namedRangeId": range,
                        "name": name + "_NR",
                        "range": {
                            "sheetId": sheetId,
                            "startRowIndex": int(sheet_range[0][1:]) - 1,
                            "endRowIndex": sheet_range[1][1:],
                            "startColumnIndex": ord(sheet_range[0][:1]) % 65,
                            "endColumnIndex": ord(sheet_range[1][:1]) % 65 + 1,
                        },
                    }
                },
            }
        ]
    }

    response = (
        service.spreadsheets()
        .batchUpdate(spreadsheetId=spreadsheetId, body=body)
        .execute()
    )

def get_named_range(spreadsheetId, range="A:F"):
    spreadsheet = get_sheet(spreadsheetId, range)
    return spreadsheet['namedRanges']

def append_empty_row_sheet(spreadsheetId, rows, range="A:F"):
    sheetId = get_sheet(spreadsheetId, range)["sheets"][0]["properties"]["sheetId"]
    body = {
        "requests": [
            {
                "appendDimension":{
                    "sheetId": sheetId,
                    "dimension": "ROWS",
                    "length": rows
                }
            }
        ]
    }
    sheet.batchUpdate(spreadsheetId=spreadsheetId, body=body).execute()