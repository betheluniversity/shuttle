import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pprint import pprint
from shuttle import app
scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name(app.config['GS_CLIENT_SECRET'], scope)

client = gspread.authorize(creds)

sheet = client.open("Bethel Shuttle Scheduling Spreadsheet").sheet1

data = sheet.get_all_records()

pprint(data)