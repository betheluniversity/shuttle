import gspread
from oauth2client.service_account import ServiceAccountCredentials
from shuttle import app
from shuttle.db.db_functions import commit_schedule_to_db


class SheetsController:
    def __init__(self):
        pass

    def send_schedule(self):
        scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]

        creds = ServiceAccountCredentials.from_json_keyfile_name(app.config['GS_CLIENT_SECRET'], scope)

        client = gspread.authorize(creds)

        sheet = client.open("Bethel Shuttle Scheduling Spreadsheet").sheet1

        list_of_lists = sheet.get_all_values()
        sent = commit_schedule_to_db(list_of_lists)
        return sent