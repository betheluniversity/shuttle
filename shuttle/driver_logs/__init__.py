from datetime import datetime

# Packages
from flask import render_template
from flask_classy import FlaskView, route, request

# Local
from shuttle.schedules.shuttle_schedules_controller import ScheduleController
from shuttle.shuttle_controller import ShuttleController


class DriverLogsView(FlaskView):
    route_base = '/logs'

    def __init__(self):
        self.sc = ShuttleController()
        self.ssc = ScheduleController()

    @route('/driver-logs')
    def shuttle_logs(self):
        self.sc.check_roles_and_route(['Administrator'])
        date_list = self.ssc.grab_dates()
        now = datetime.now()
        date = now.strftime('%b-%d-%Y')
        return render_template('driver_logs/driver_logs.html', **locals())

    @route('/shuttle-logs', methods=['GET', 'POST'])
    def selected_shuttle_logs(self):
        json_data = request.get_json()
        date = json_data['date']
        name_sort = json_data['sort']
        selected_logs = self.ssc.grab_selected_logs(date, name_sort)
        shuttle_logs = selected_logs[0]
        break_logs = selected_logs[1]
        completed_requests = selected_logs[2]
        deleted_requests = selected_logs[3]
        return render_template('driver_logs/load_logs.html', **locals())
