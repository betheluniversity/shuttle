from datetime import datetime
from io import StringIO
import csv

# Packages
from flask import render_template
from flask_classy import FlaskView, route, request, Response

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


    @route('/download-logs/<date>/<name_sort>', methods=['GET', 'POST'])
    def export_logs(self, date, name_sort):
        selected_logs = self.ssc.grab_selected_logs(date, name_sort)
        current_date = datetime.now().strftime('%m/%d/%Y')
        date = datetime.strptime(date, '%b-%d-%Y').strftime('%m/%d/%y')
        csv_name = 'driver_logs_' + date
        log_type = ['Shuttle Logs', 'Break Logs', 'Completed Logs', 'Deleted Logs']

        def generate():
            # sets up a buffer and start file
            data = StringIO()
            writer = csv.writer(data)
            new_line = []
            writer.writerow([csv_name, 'Exported on: ' + current_date])
            writer.writerow(new_line)

            for i in range(len(selected_logs)):
                for j in range(len(selected_logs[i])):
                    # grabs a log, adds its data if its not empty
                    log_dict = selected_logs[i][j]
                    if log_dict:
                        dict_writer = csv.DictWriter(data, fieldnames=log_dict.keys())
                        if j == 0:
                            header_space = ['----------------------------------'] * 10
                            writer.writerow(header_space)
                            writer.writerow(log_type[i])
                            dict_writer.writeheader()
                        dict_writer.writerow(log_dict)
                        yield data.getvalue()
                        data.seek(0)
                        data.truncate(0)
                writer.writerow(new_line)
            data.close()

        file_headers = {"Content-disposition": "attachment; filename=" + csv_name + '.csv'}
        return Response(generate(),
                        mimetype='text/csv',
                        headers=file_headers)
