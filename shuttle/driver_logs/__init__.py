from datetime import datetime

# Packages
from flask import render_template
from flask_classy import FlaskView, route, request, Response
from io import StringIO
import csv

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

    @route('/download-logs/<date>/<sort>', methods=['GET', 'POST'])
    def download_logs(self, date, sort):
        selected_logs = self.ssc.grab_selected_logs(date, sort)

        def generate():
            data = StringIO()
            for i in range(len(selected_logs)):
                for j in range(len(selected_logs[i])):
                    w = csv.DictWriter(data, fieldnames=selected_logs[i][j].keys())
                    w.writerow(selected_logs[i][j])
                    yield data.getvalue()
                    data.seek(0)
                    data.truncate(0)

        file_headers = {"Content-disposition": "attachment; filename=" 'export.csv'}
        return Response(generate(),
                        mimetype='text/csv',
                        headers=file_headers)