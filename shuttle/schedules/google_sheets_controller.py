import gspread
from oauth2client.service_account import ServiceAccountCredentials
from shuttle import app
from shuttle.db import db_functions as db
from flask import session as flask_session


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
        list_of_times = sheet.get_all_values()
        locations = SheetsController.grab_locations(self)
        sent = db.commit_schedule(list_of_times, locations)
        return sent

    def grab_locations(self):
        client = SheetsController.credentials(self)
        sheet = client.open("Bethel Shuttle Scheduling Spreadsheet").worksheet("Shuttle Locations")
        locations = sheet.col_values(1)
        return locations

    # This method sets the alert for when one is needed next
    def set_alert(self, message_type, message):
        flask_session['ALERT'].append({
            'type': message_type,
            'message': message
        })
        flask_session.modified = True
