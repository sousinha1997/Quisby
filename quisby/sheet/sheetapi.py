from googleapiclient.discovery import build
from google.oauth2 import service_account

SCOPES=['https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/spreadsheets.readonly','https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'credentials.json'

creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build("sheets", "v4", credentials=creds)
sheet = service.spreadsheets()
