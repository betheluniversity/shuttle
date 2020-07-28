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
        # scheduled shuttle logs are shown by default when the page is first loaded
        date_list_scheduled = self.ssc.grab_dates('Scheduled Shuttle Logs')
        date_list_on_call = self.ssc.grab_dates('On Call Shuttle Logs')
        now = datetime.now()
        date = now.strftime('%b-%d-%Y')
        return render_template('driver_logs/driver_logs.html', **locals())

    @route('/shuttle-logs', methods=['GET', 'POST'])
    def selected_shuttle_logs(self):
        json_data = request.get_json()
        date = json_data['date']
        name_sort = json_data['sort']
        # Shows scheduled logs by default
        if json_data['log'] == 'On Call Shuttle Logs':
            selected_logs = self.ssc.grab_selected_on_call_logs(date, name_sort)
            completed_requests = selected_logs[0]
            deleted_requests = selected_logs[1]
            return render_template('driver_logs/load_on_call_logs.html', **locals())
        else:
            selected_logs = self.ssc.grab_selected_logs(date, name_sort)
            shuttle_logs = selected_logs[0]
            break_logs = selected_logs[1]
            return render_template('driver_logs/load_scheduled_logs.html', **locals())
