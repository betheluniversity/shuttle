# Packages
from flask import render_template
from flask_classy import FlaskView, route

# Local
from shuttle.db import db_functions as db
from shuttle.schedules.google_sheets_controller import SheetsController
from shuttle.schedules.shuttle_schedules_controller import ScheduleController
from shuttle.shuttle_controller import ShuttleController


class SchedulesView(FlaskView):
    def __init__(self):
        self.sc = ShuttleController()
        self.ssc = ScheduleController()
        self.shc = SheetsController()

    @route('/shuttle-schedule')
    def schedule(self):
        # Shows schedule from database
        schedule = self.ssc.grab_db_schedule()
        return render_template('schedules/shuttle_schedule.html', **locals())

    @route('/send-schedule')
    def send_schedule_path(self):
        self.sc.check_roles_and_route(['Administrator'])
        spreadsheet = self.shc.grab_schedule()
        locations = self.shc.grab_locations()
        sent = db.commit_schedule(spreadsheet, locations)
        if sent == "success":
            self.sc.set_alert('success', 'The schedule has been submitted')
        elif sent == 'no match':
            self.sc.set_alert('danger', 'Data in calendar does not match specified format')
        else:
            self.sc.set_alert('danger', 'Something went wrong. Please call the ITS Help '
                                        'Desk at 651-638-6500 for support')
        return sent
