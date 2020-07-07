from flask import session as flask_session, abort
import re
from shuttle.db import db_functions as db
from datetime import datetime
from shuttle.schedules import SheetsController


class ShuttleController(object):
    def __init__(self):
        self.shc = SheetsController()

    # Used to make sure the correct roles are viewing the route
    def check_roles_and_route(self, allowed_roles):
        for role in allowed_roles:
            if role in flask_session['USER-ROLES']:
                return True
        abort(403)

    # This method get's the current alert (if there is one) and then resets alert to nothing
    def get_alert(self):
        if 'ALERT' not in flask_session.keys():
            flask_session['ALERT'] = []
        alert_return = flask_session['ALERT']
        flask_session['ALERT'] = []
        return alert_return

    # This method sets the alert for when one is needed next
    def set_alert(self, message_type, message):
        flask_session['ALERT'].append({
            'type': message_type,
            'message': message
        })
        flask_session.modified = True

    def grab_check_in_driver_data(self):
        data = db.get_last_location()
        return data

    # Method takes the last time checked in by the driver and uses that to find the next closest
    # time based on the spreadsheet. Method assumes the location is the first column in the spreadsheet
    def grab_current_route(self):
        try:
            time = db.get_last_location()['time']
            latest_time = datetime.strptime(time, '%I:%M %p')
            schedule = self.shc.grab_schedule()
            closest_time_greater = -1
            next_stop = {'location': 'No more stops today', 'time': 'N/A'}
            for i in range(len(schedule)):
                for j in range(len(schedule[i])):
                    # All times are converted to the same format so they can be compared
                    if j != 0 and re.search("^[\d]:[\d][\d]$", schedule[i][j]) or re.search("^[\d][\d]:[\d][\d]$",
                                                                                            schedule[i][j]):
                        split_time = schedule[i][j].split(':')
                        if int(split_time[0]) == 12 or 1 <= int(split_time[0]) < 6:
                            schedule_time = (schedule[i][j] + ' PM')
                        else:
                            schedule_time = (schedule[i][j] + ' AM')
                        schedule_time = datetime.strptime(schedule_time, '%I:%M %p')
                        # Checks for the next closest time that is greater than the driver's last check in
                        if schedule_time > latest_time:
                            if closest_time_greater == -1:
                                closest_time_greater = schedule_time
                            else:
                                if schedule_time < closest_time_greater:
                                    closest_time_greater = schedule_time
                                    next_stop = {
                                        'location': schedule[i][0],
                                        'time': closest_time_greater.strftime('%I:%M %p').lstrip("0").replace(" 0",
                                                                                                              " ")
                                    }
            return next_stop
        except:
            return {'location': 'Error', 'time': 'Error'}

