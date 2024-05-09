from googleapiclient.discovery import build
from google.oauth2 import service_account
import os
import sys

from quisby import custom_logger

home_dir = os.getenv("HOME")
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/spreadsheets.readonly',
          'https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = home_dir + '/.quisby/config/credentials.json'
DISCOVERY_SERVICE_URL = 'https://sheets.googleapis.com/$discovery/rest?version=v4'


def check_google_credentials_exist():
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        custom_logger.error("Google service account credentials not found at " + home_dir + "/.quisby/config/")
        if not os.path.exists(home_dir + "/.quisby/config/"):
            os.makedirs(home_dir + "/.quisby/config/")
        sys.exit(1)


check_google_credentials_exist()
creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build("sheets", "v4", credentials=creds, discoveryServiceUrl=DISCOVERY_SERVICE_URL)
sheet = service.spreadsheets()
