from googleapiclient.discovery import build
from google.oauth2 import service_account
import os

sheet = None
creds = None

def initialise_google_api_service():
    global sheet
    global creds
    if sheet is None:
        home_dir = os.getenv("HOME")
        SCOPES=['https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/spreadsheets.readonly','https://www.googleapis.com/auth/drive']
        SERVICE_ACCOUNT_FILE = home_dir+'/.quisby/config/credentials.json'
        DISCOVERY_SERVICE_URL = 'https://sheets.googleapis.com/$discovery/rest?version=v4'
        creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        service = build("sheets", "v4", credentials=creds,discoveryServiceUrl=DISCOVERY_SERVICE_URL)
        sheet = service.spreadsheets()

