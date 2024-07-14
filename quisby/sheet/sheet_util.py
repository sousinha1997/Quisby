from quisby import custom_logger
from googleapiclient.discovery import build
from quisby.sheet.sheetapi import sheet, creds
from quisby.util import read_config


def check_sheet_exists(sheet_info, test_name):
    """"""
    for sheet_prop in sheet_info:
        if test_name == sheet_prop["properties"]["title"]:
            return True

    return False


def permit_users(spreadsheetId, notification):
    custom_logger.info("Providing write access to specified users")
    users = read_config("access", "users").split(",")
    if users == ['']:
        return
    drive_api = build('drive', 'v3', credentials=creds)
    for user in users:
        try:
            domain_permission = {
                'type': 'user',
                'role': 'writer',
                'emailAddress': user,
                'sendNotificationEmails': notification
            }
            req = drive_api.permissions().create(
                fileId=spreadsheetId,
                body=domain_permission,
                fields="id"
            )

            req.execute()
        except Exception as exc:
            custom_logger.debug(str(exc))
            custom_logger.error("Unable to provide access to this user : "+user)


def create_spreadsheet(spreadsheet_name, test_name, notification):
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
    spreadsheetid = spreadsheet["spreadsheetId"]
    permit_users(spreadsheetid, notification)
    return spreadsheetid


def get_sheet(spreadsheetId, test_name,range="!a:z"):

    if test_name == []:
        #create sheet
        return sheet.get(spreadsheetId=spreadsheetId).execute()
    else:
        return sheet.get(spreadsheetId=spreadsheetId,ranges=test_name+range).execute()


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
        custom_logger.info("Sheet for this benchmark doesn't exist. Creating...")
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

    custom_logger.info(response)


def clear_sheet_data(spreadsheetid, range):
    sheet.values().clear(spreadsheetId=spreadsheetid, range=range, body={}).execute()


def clear_sheet_charts(spreadsheetid, range):

    sheet_properties = get_sheet(spreadsheetid, range)

    if "charts" in sheet_properties["sheets"][0]:
        for chart in sheet_properties["sheets"][0]["charts"]:

            requests = {"deleteEmbeddedObject": {"objectId": chart["chartId"]}}

            body = {"requests": requests}

            sheet.batchUpdate(spreadsheetId=spreadsheetid, body=body).execute()


def get_named_range(spreadsheetId, range="A:F"):
    spreadsheet = get_sheet(spreadsheetId, range)

    return spreadsheet['namedRanges']


def append_empty_row_sheet(spreadsheetId, rows,range):
    
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


def append_empty_col_sheet(spreadsheetId, cols, range):
    sheetId = get_sheet(spreadsheetId, range)["sheets"][0]["properties"]["sheetId"]

    body = {
        "requests": [
            {
                "appendDimension": {
                    "sheetId": sheetId,
                    "dimension": "COLUMNS",
                    "length": cols
                }
            }
        ]
    }

    sheet.batchUpdate(spreadsheetId=spreadsheetId, body=body).execute()