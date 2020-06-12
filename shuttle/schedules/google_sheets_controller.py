import gspread
from oauth2client.service_account import ServiceAccountCredentials
from shuttle import app
from shuttle.db.db_functions import commit_schedule_to_db


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
        client = SheetsController.credentials(self)
        sheet = client.open("Bethel Shuttle Scheduling Spreadsheet").worksheet("Shuttle Schedule")
        list_of_lists = sheet.get_all_values()
        locations = SheetsController.grab_locations(self)
        sent = commit_schedule_to_db(list_of_lists, locations)
        return sent

    def grab_locations(self):
        client = SheetsController.credentials(self)
        sheet = client.open("Bethel Shuttle Scheduling Spreadsheet").worksheet("Shuttle Locations")
        list_of_lists = sheet.col_values(1)
        return list_of_lists
