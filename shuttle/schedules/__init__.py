import datetime

from flask import render_template, request
from flask_classy import FlaskView, route
from shuttle.db import db_functions as db
from shuttle.shuttle_controller import ShuttleController
from shuttle.schedules.shuttle_schedules_controller import ScheduleController


class SchedulesView(FlaskView):
    def __init__(self):
        self.sc = ShuttleController()
        self.ssc = ScheduleController()

    @route('/shuttle-stats')
    def stats(self):
        return render_template('/schedules/shuttle_stats.html')

    @route('/request-shuttle')
    def request(self):
        self.sc.check_roles_and_route(['Administrator', 'Driver', 'User'])
        return render_template('/schedules/request_shuttle.html')

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
        grabbed_logs = self.ssc.grab_logs()
        logs = grabbed_logs[0]
        date_list = grabbed_logs[1]
        return render_template('schedules/driver_logs.html', **locals())

    @route('/shuttle-logs', methods=['GET', 'POST'])
    def shuttle_logs(self):
        json_data = request.get_json()
        if json_data == "today's date":
            now = datetime.datetime.now()
            date = now.strftime('%Y-%m-%d')
        else:
            date = json_data['date']
        selected_logs = self.ssc.grab_selected_logs(date)
        shuttle_logs = selected_logs[0]
        break_logs = selected_logs[1]
        return render_template('schedules/load_logs.html', **locals())
