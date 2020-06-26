import gspread
from oauth2client.service_account import ServiceAccountCredentials

from shuttle import app


class SheetsController:
    def __init__(self):
        pass

    def credentials(self):
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/spreadsheets',
                 'https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(app.config['GS_CLIENT_SECRET'], scope)
        client = gspread.authorize(creds)
        return client

    def grab_schedule(self):
        client = self.credentials()
        sheet = client.open('Bethel Shuttle Scheduling Spreadsheet').worksheet('Shuttle Schedule')
        list_of_times = sheet.get_all_values()
        return list_of_times

    def grab_locations(self):
        client = self.credentials()
        sheet = client.open('Bethel Shuttle Scheduling Spreadsheet').worksheet('Shuttle Locations')
        locations = sheet.col_values(1)
        return locations
