from googleapiclient.discovery import build
from google.oauth2 import service_account

import os

SCOPES=['https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/spreadsheets.readonly','https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = os.path.join(os.environ['quisby_conf_dir'],'credentials.json')
DISCOVERY_SERVICE_URL = 'https://sheets.googleapis.com/$discovery/rest?version=v4'
creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build("sheets", "v4", credentials=creds,discoveryServiceUrl=DISCOVERY_SERVICE_URL)
drive_service = build("drive", "v3", credentials = creds)
sheet = service.spreadsheets()
file = drive_service.files()