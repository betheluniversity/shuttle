import gspread
from oauth2client.service_account import ServiceAccountCredentials

from shuttle import app
from shuttle.db import db_functions as db


class SheetsController:
    def __init__(self):
        pass

    def credentials(self):
        scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
                 "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(app.config['GS_CLIENT_SECRET'], scope)
        client = gspread.authorize(creds)
        return client

    def send_schedule(self):
        client = self.credentials()
        sheet = client.open("Bethel Shuttle Scheduling Spreadsheet").worksheet("Shuttle Schedule")
        list_of_times = sheet.get_all_values()
        locations = self.grab_locations()
        sent = db.commit_schedule(list_of_times, locations)
        return sent

    def grab_locations(self):
        client = self.credentials()
        sheet = client.open("Bethel Shuttle Scheduling Spreadsheet").worksheet("Shuttle Locations")
        locations = sheet.col_values(1)
        return locations
