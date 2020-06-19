from flask import render_template, request
from flask_classy import FlaskView, route
from shuttle.db import db_functions as db
from shuttle.shuttle_controller import ShuttleController

shuttle_logs = {}


class SchedulesView(FlaskView):
    def __init__(self):
        self.sc = ShuttleController()

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
        global shuttle_logs
        shuttle_logs = db.get_shuttle_logs()
        date = 0
        date_list = []
        for i in range(len(shuttle_logs)):
            real_name = db.username_search(shuttle_logs[i]['username'])
            shuttle_logs[i]['name'] = real_name[0]['firstName'] + " " + real_name[0]['lastName']
            shuttle_logs[i]['log_date'] = str(shuttle_logs[i]['log_date']).split(" ")[0]
            if date != shuttle_logs[i]['log_date']:
                date = shuttle_logs[i]['log_date']
                date_list.append(date)
        return render_template('schedules/driver_logs.html', **locals())

    @route('/shuttle-logs', methods=['GET', 'POST'])
    def shuttle_logs(self):
        json_data = request.get_json()
        date = json_data['date']
        logs = shuttle_logs
        if date == '':
            self.sc.set_alert('danger', 'Please select a log')
            return "no log"
        return render_template('schedules/load_logs.html', **locals())
