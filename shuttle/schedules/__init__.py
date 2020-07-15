from flask import render_template, session
from flask_classy import FlaskView, route, request
from shuttle.db import db_functions as db
import json

import re
from datetime import datetime
from shuttle.schedules.google_sheets_controller import SheetsController
from shuttle.shuttle_controller import ShuttleController
from shuttle.schedules.shuttle_schedules_controller import ScheduleController
from shuttle.wsapi.wsapi_controller import WSAPIController


class SchedulesView(FlaskView):
    def __init__(self):
        self.sc = ShuttleController()
        self.ssc = ScheduleController()
        self.shc = SheetsController()
        self.wsapi = WSAPIController()

    @route('/shuttle-schedule')
    def schedule(self):
        schedule = self.shc.grab_schedule()
        return render_template('schedules/shuttle_schedule.html', **locals())

    @route('/request-shuttle')
    def request(self):
        self.sc.check_roles_and_route(['Administrator', 'Driver', 'User'])
        locations = self.shc.grab_locations()
        active_requests = db.number_active_requests()
        if active_requests['requested-pick-up']:
            position_in_waitlist = db.get_position_in_waitlist()[0]['rownumber']
        return render_template('schedules/request_shuttle.html', **locals())

    @route('/edit-schedule')
    def edit_schedule(self):
        self.sc.check_roles_and_route(['Administrator'])
        return render_template('schedules/edit_shuttle_schedule.html')

    @route('/driver-check-in')
    def check_in(self):
        self.sc.check_roles_and_route(['Administrator', 'Driver'])
        requests = db.get_requests()
        active_requests = db.number_active_requests()['waitlist-num']
        driver_select = session['DRIVER-SELECT']
        return render_template('schedules/shuttle_driver_check_in.html', **locals())

    # Loads in the selected driver view
    @route('/driver-view', methods=['GET', 'POST'])
    def load_driver_view(self):
        json_data = request.get_json()
        load = ''
        session['DRIVER-SELECT'] = json_data['view']
        if json_data['view'] == 'Location Check In':
            load = 'locations'
            locations = self.shc.grab_locations()
            current_break_status = db.break_status()
            return render_template('loaded_views/load_dci_locations.html', **locals())
        if json_data['view'] == 'Active Requests':
            load = 'requests'
            requests = db.get_requests()
            active_requests = db.number_active_requests()['waitlist-num']
            current_break_status = db.break_status()
            return render_template('loaded_views/load_dci_requests.html', **locals())

    def select_user_roles(self, username, first_name, last_name):
        # roles = self.uc.get_all_roles()
        # existing_user = self.uc.get_user_by_username(username)
        if existing_user:  # User exists in system
            if existing_user.deletedAt:  # Has been deactivated in the past
                success = self.uc.activate_existing_user(existing_user.id)
                if success:
                    message = 'This user has been deactivated in the past, but now they are reactivated with their ' \
                              'same roles.'
                else:
                    message = 'Failed to reactivate the user.'
        return render_template('users/select_user_roles.html', **locals())

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
        now = datetime.now()
        date = now.strftime('%b-%d-%Y')
        logs = grabbed_logs[0]
        date_list = grabbed_logs[1]
        return render_template('schedules/driver_logs.html', **locals())

    @route('/users')
    def users(self):
        self.sc.check_roles_and_route(['Administrator'])
        shuttle_user = db.get_users()

        current_user = session['USERNAME']

        for key in shuttle_user:
            shuttle_user[key]['name'] = db.username_search(shuttle_user[key]['username'])[0]['firstName'] + \
                                        ' ' + db.username_search(shuttle_user[key]['username'])[0]['lastName']
        return render_template('/schedules/users.html', **locals())

    @route("/search-users", methods=['POST'])
    def search_users(self):
        first_name = json.loads(request.data).get('firstName')
        last_name = json.loads(request.data).get('lastName')
        try:
            if first_name == '' and last_name == '':
                self.sc.set_alert('danger', 'Please enter a valid name.')
                return 'error'
            results = self.wsapi.get_username_from_name(first_name, last_name)
        except:
            self.sc.set_alert('danger', 'Something went wrong.')
            return 'error'
        return render_template('loaded_views/user_search_results.html', **locals())

    @route('load-user-data', methods=['POST', 'GET'])
    def load_user_data(self):
        self.sc.check_roles_and_route(['Administrator'])
        username = json.loads(request.data).get('username')
        return render_template('/loaded_views/user_modal.html', **locals())

    @route('/add-user-page')
    def add_user_page(self):
        return render_template('loaded_views/add_user.html')

    @route('delete-user', methods=['POST'])
    def delete_user(self):
        self.sc.check_roles_and_route(['Administrator'])
        username = json.loads(request.data).get('username')
        if username != session['USERNAME']:
            result = db.delete_user(username)
            if result == 'success':
                self.sc.set_alert('success', 'User '+ username + ' successfully deleted.')
            return result
        else:
            self.sc.set_alert('danger', 'You cannot delete your own account.')
            return 'error'

    @route('edit-user', methods=['POST'])
    def edit_user(self):
        self.sc.check_roles_and_route(['Administrator'])
        username = json.loads(request.data).get('username')
        role = json.loads(request.data).get('role')
        if username != session['USERNAME']:
            result = db.change_user_role(username, role)
            return result
        else:
            self.sc.set_alert('danger', 'You cannot edit your own account.')
            return 'error'

    @route('add-user', methods=['POST'])
    def add_user(self):
        self.sc.check_roles_and_route(['Administrator'])
        username = json.loads(request.data).get('username')
        role = json.loads(request.data).get('role')
        result = db.add_user(username, role)
        if result == 'success':
            self.sc.set_alert('success', 'User successfully added.')
        else:
            self.sc.set_alert('danger', 'Something went wrong trying to add that user.')
        return result

    @route('/shuttle-logs', methods=['GET', 'POST'])
    def shuttle_logs(self):
        json_data = request.get_json()
        date = json_data['date']
        if json_data['sort'] == 'Sort By Name':
            sort = json_data['sort']
        else:
            sort = ''
        selected_logs = self.ssc.grab_selected_logs(date, sort)
        shuttle_logs = selected_logs[0]
        break_logs = selected_logs[1]
        return render_template('loaded_views/load_logs.html', **locals())

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
                    if j != 0 and re.search("^[\d]:[\d][\d]$", schedule[i][j]) or re.search("^[\d][\d]:[\d][\d]$",
                                                                                            schedule[i][j]):
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
