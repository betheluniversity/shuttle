import re
from datetime import datetime

# Local
from shuttle.db import db_functions as db
from shuttle.schedules import SheetsController, ScheduleController


class HomePageController:
    def __init__(self):
        self.shc = SheetsController()
        self.ssc = ScheduleController()

    def grab_check_in_driver_data(self):
        data = db.get_last_location()
        if data['date'] == 'Error':
            return data
        current_date = datetime.now().strftime('%d-%b-%y')
        if data['date'] != current_date:
            data['location'] = 'No check ins for today'
            data['time'] = 'N/A'
        return data

    # Method takes the last time checked in by the driver and uses that to find the next closest
    # time based on the spreadsheet. Method assumes the location is the first row in the spreadsheet
    def grab_current_route(self):
        try:
            day = datetime.now().strftime('%a')
            # If it is the weekend, show there are no stops
            if day == 'Sun' or day == 'Sat':
                return {'location': 'No stops on the weekend', 'time': 'N/A'}
            latest_time = datetime.strptime(datetime.today().strftime('%I:%M %p'), '%I:%M %p')
            schedule = self.ssc.grab_db_schedule()
            next_stop = {'location': 'No more stops today', 'time': 'N/A'}
            for i in range(len(schedule)):
                for j in range(len(schedule[i])):
                    # All times are converted to the same format so they can be compared
                    if i != 0 and re.search("^[\d]:[\d][\d][\s](A|P)[M]$", schedule[i][j]) or \
                            re.search("^[\d][\d]:[\d][\d][\s](A|P)[M]$", schedule[i][j]):
                        schedule_time = datetime.strptime(schedule[i][j], '%I:%M %p')
                        # Checks for the next closest time that is greater than the driver's last check in
                        if schedule_time > latest_time:
                            next_stop = {
                                'location': schedule[0][j],
                                'time': schedule_time.strftime('%-I:%M %p').lower()
                            }
                            # The next biggest time is automatically the next time with
                            # security's schedule format so we can return
                            return next_stop
            return next_stop
        except:
            return {'location': 'Error', 'time': 'Error'}
