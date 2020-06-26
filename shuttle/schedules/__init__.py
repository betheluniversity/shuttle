from datetime import datetime
from flask import render_template, request
from flask_classy import FlaskView, route
from shuttle.db import db_functions as db
from shuttle.schedules.google_sheets_controller import SheetsController
from shuttle.shuttle_controller import ShuttleController
from shuttle.schedules.shuttle_schedules_controller import ScheduleController


class SchedulesView(FlaskView):
    def __init__(self):
        self.sc = ShuttleController()
        self.ssc = ScheduleController()
        self.shc = SheetsController()

    @route('/shuttle-schedule')
    def schedule(self):
        schedule = self.shc.grab_schedule()
        return render_template('/schedules/shuttle_schedule.html', **locals())

    @route('/request-shuttle')
    def request(self):
        self.sc.check_roles_and_route(['Administrator', 'Driver', 'User'])
        locations = self.shc.grab_locations()
        return render_template('/schedules/request_shuttle.html', **locals())

    @route('/edit-schedule')
    def edit_schedule(self):
        self.sc.check_roles_and_route(['Administrator'])
        return render_template('schedules/edit_shuttle_schedule.html')

    @route('/driver-check-in')
    def check_in(self):
        self.sc.check_roles_and_route(['Administrator', 'Driver'])
        locations = self.shc.grab_locations()
        return render_template('schedules/shuttle_driver_check_in.html', **locals())

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
            now = datetime.now()
            date = now.strftime('%Y-%m-%d')
        else:
            date = json_data['date']
        selected_logs = self.ssc.grab_selected_logs(date)
        shuttle_logs = selected_logs[0]
        break_logs = selected_logs[1]
        return render_template('schedules/load_logs.html', **locals())

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

    @route('/send-schedule', methods=['GET', 'POST'])
    def send_shuttle_request_path(self):
        self.sc.check_roles_and_route(['Administrator', 'Driver', 'User'])
        json_data = request.get_json()
        response = db.commit_shuttle_request(json_data['location'])
        if response == 'success':
            self.sc.set_alert('success', 'Your request has been submitted')
        elif response == 'bad location':
            self.sc.set_alert('danger', 'Please select a location')
        elif response == 'user has active request':
            self.sc.set_alert('danger', 'You already have an active request')
        else:
            self.sc.set_alert('danger', 'Something went wrong. Please call the ITS Help '
                                        'Desk at 651-638-6500 for support')
        return response

    def check_waitlist(self):
        self.sc.check_roles_and_route(['Administrator', 'Driver', 'User'])
        num_waiting = db.number_active_requests()
        return num_waiting

    @route('/driver-check', methods=['GET', 'POST'])
    def delete_request(self):
        self.sc.check_roles_and_route(['Administrator', 'Driver', 'User'])
        request_to_delete = db.delete_current_request()
        if request_to_delete == 'success':
            self.sc.set_alert('success', 'Your request has been deleted')
        else:
            self.sc.set_alert('danger', 'Something went wrong. Please try again or '
                                        'call the ITS Help Desk at 651-638-6500')
        return request_to_delete

    @route('/driver-check', methods=['Get', 'POST'])
    def send_driver_check_in_info(self):
        self.sc.check_roles_and_route(['Administrator', 'Driver'])
        json_data = request.get_json()
        if 'location' in json_data.keys():
            response = db.commit_driver_check_in(json_data['location'], json_data['direction'], '')
            if response == 'success arrival':
                self.sc.set_alert('success', 'Your arrival has been recorded')
            elif response == 'success departure':
                self.sc.set_alert('success', 'Your departure has been recorded')
        else:
            response = db.commit_driver_check_in('', '', json_data['break'])
        if response == 'bad location':
            self.sc.set_alert('danger', 'Please select a location')
        elif response == 'Error':
            self.sc.set_alert('danger', 'Something went wrong. Please try again or '
                                        'call the ITS Help Desk at 651-638-6500')
        return response

    @route('/recent-data', methods=['GET', 'POST'])
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
                    if j != 0 and ':' in schedule[i][j]:
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
                                    next_stop = {'location': schedule[i][0],
                                                 'time': closest_time_greater.strftime('%I:%M %p')}
            return next_stop
        except:
            return {'location': 'Error', 'time': 'Error'}
