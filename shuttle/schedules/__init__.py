import datetime
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

    @route('/shuttle-stats')
    def stats(self):
        return render_template('schedules/shuttle_stats.html')

    @route('/request-shuttle')
    def request(self):
        self.sc.check_roles_and_route(['Administrator', 'Driver', 'User'])
        locations = self.shc.grab_locations()
        active_requests = db.number_active_requests()
        if active_requests['requested-pick-up']:
            position_in_waitlist = db.get_position_in_waitlist()[0]['rownumber']
        return render_template('schedules/request_shuttle.html', **locals())

    @route('/shuttle-schedules')
    def schedule(self):
        self.sc.check_roles_and_route(['Administrator'])
        return render_template('schedules/shuttle_schedules.html')

    @route('/driver-check-in')
    def check_in(self):
        self.sc.check_roles_and_route(['Administrator', 'Driver'])
        requests = db.get_requests()
        active_requests = db.number_active_requests()['waitlist-num']
        return render_template('schedules/shuttle_driver_check_in.html', **locals())

    # Loads in the selected driver view
    @route('/driver-view', methods=['GET', 'POST'])
    def load_driver_view(self):
        json_data = request.get_json()
        load = ''
        if json_data['view'] == 'Location check in':
            load = 'locations'
            locations = self.shc.grab_locations()
            return render_template('loaded_views/load_dci_locations.html', **locals())
        if json_data['view'] == 'Active requests':
            load = 'requests'
            requests = db.get_requests()
            active_requests = db.number_active_requests()['waitlist-num']
            return render_template('loaded_views/load_dci_requests.html', **locals())
        if json_data['view'] == 'Break check in':
            load = 'break'
            current_break_status = db.break_status()
            return render_template('loaded_views/load_dci_break.html', **locals())

    @route('/complete-request', methods=['GET', 'POST'])
    def complete_request(self):
        json_data = request.get_json()
        username = json_data['username']
        results = db.complete_shuttle_request(username)
        if results == 'success':
            self.sc.set_alert('success', 'The request has been completed')
        else:
            self.sc.set_alert('danger', 'Something went wrong. Please call the ITS Help '
                                        'Desk at 651-638-6500 for support')
        return results

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
            date = now.strftime('%b-%d-%Y')
        else:
            date = json_data['date']
        selected_logs = self.ssc.grab_selected_logs(date)
        shuttle_logs = selected_logs[0]
        break_logs = selected_logs[1]
        return render_template('loaded_views/load_logs.html', **locals())

    def send_schedule_path(self):
        self.sc.check_roles_and_route(['Administrator'])
        sent = self.shc.send_schedule()
        if sent == 'success':
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
        response = db.commit_shuttle_request(json_data['pick-up-location'], json_data['drop-off-location'])
        if response == 'success':
            self.sc.set_alert('success', 'Your request has been submitted')
        elif response == 'same location':
            self.sc.set_alert('danger', 'Please select two different locations')
        elif response == 'no location':
            self.sc.set_alert('danger', 'Please select a location')
        else:
            self.sc.set_alert('danger', 'Something went wrong. Please call the ITS Help '
                                        'Desk at 651-638-6500 for support')
        return response

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
        response = db.commit_driver_check_in(json_data['location'], json_data['direction'])
        if response == 'success arrival':
            self.sc.set_alert('success', 'Your arrival at ' + json_data['location'] + ' has been recorded')
        elif response == 'success departure':
            self.sc.set_alert('success', 'Your departure from ' + json_data['location'] + ' has been recorded')
        elif response == 'bad location':
            self.sc.set_alert('danger', 'Please select a location')
        else:
            self.sc.set_alert('danger', 'Something went wrong. Please try again or '
                                        'call the ITS Help Desk at 651-638-6500')
        return response

    @route('/send-break-info', methods=['Get', 'POST'])
    def send_driver_break_info(self):
        self.sc.check_roles_and_route(['Administrator', 'Driver'])
        json_data = request.get_json()
        response = db.commit_break(json_data['break'])
        if response == 'on break success':
            self.sc.set_alert('success', 'Clock out recorded successfully')
        elif response == 'off break success':
            self.sc.set_alert('success', 'Clock in recorded successfully')
        elif response == 'error: not on break':
            self.sc.set_alert('danger', 'Can\'t clock in because you are not on break')
        elif response == 'error: already on break':
            self.sc.set_alert('danger', 'Can\'t clock out because you are already on break')
        else:
            self.sc.set_alert('danger', 'Something went wrong. Please try again or '
                                        'call the ITS Help Desk at 651-638-6500')
        return response
