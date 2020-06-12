from flask import render_template, request
from flask_classy import FlaskView, route
from shuttle.db.db_functions import number_active_in_db, commit_shuttle_request_to_db
from shuttle.schedules.google_sheets_controller import SheetsController

from shuttle.shuttle_controller import ShuttleController


class SchedulesView(FlaskView):
    def __init__(self):
        self.sc = ShuttleController()

    @route('/shuttle-stats')
    def stats(self):
        return render_template('/schedules/shuttle_stats.html')

    @route('/request-shuttle')
    def request(self):
        location_list = SheetsController.grab_locations(self)
        self.sc.check_roles_and_route(['Administrator', 'Driver', 'User'])
        return render_template('/schedules/request_shuttle.html', locations=location_list)

    @route('/shuttle-schedules')
    def schedule(self):
        self.sc.check_roles_and_route(['Administrator'])
        return render_template('schedules/shuttle_schedules.html')

    @route('/driver-check-in')
    def check_in(self):
        self.sc.check_roles_and_route(['Administrator', 'Driver'])
        return render_template('schedules/shuttle_driver_check_in.html')

    @route('/driver-logs')
    def logs(self):
        self.sc.check_roles_and_route(['Administrator'])
        return render_template('schedules/driver_logs.html')

    def send_schedule_path(self):
        sent = SheetsController.send_schedule(self)
        return sent

    @route('/send-schedule', methods=['Get', 'POST'])
    def send_shuttle_request_path(self):
        jsonData = request.get_json()
        response = commit_shuttle_request_to_db(jsonData['location'])
        return response

    def check_waitlist(self):
        num_waiting = number_active_in_db()
        return num_waiting


