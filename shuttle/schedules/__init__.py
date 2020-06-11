from flask import render_template, request
from flask_classy import FlaskView, route
from shuttle.db.db_functions import commit_shuttle_request_to_db
from shuttle.schedules.google_sheets_controller import SheetsController


class SchedulesView(FlaskView):
    @route('/shuttle-stats')
    def stats(self):
        return render_template('/schedules/shuttle_stats.html')

    @route('/request-shuttle')
    def request(self):
        return render_template('/schedules/request_shuttle.html')

    @route('/shuttle-schedules')
    def schedule(self):
        return render_template('schedules/shuttle_schedules.html')

    @route('/driver-check-in')
    def check_in(self):
        return render_template('schedules/shuttle_driver_check_in.html')

    @route('/driver-logs')
    def logs(self):
        return render_template('schedules/driver_logs.html')

    def send_schedule_path(self):
        sent = SheetsController.send_schedule(self)
        return sent

    @route('/send-schedule', methods=['Get', 'POST'])
    def send_shuttle_request_path(self):
        jsonData = request.get_json()
        commit_shuttle_request_to_db(jsonData['location'])
        return "success"
