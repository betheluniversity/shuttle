# Packages
from flask import render_template, session
from flask_classy import FlaskView, route, request

# Local
from shuttle.db import db_functions as db
from shuttle.homepage.homepage_controller import HomePageController
from shuttle.schedules.google_sheets_controller import SheetsController
from shuttle.shuttle_controller import ShuttleController


class DriverCheckInView(FlaskView):
    route_base = '/driver'

    def __init__(self):
        self.sc = ShuttleController()
        self.shc = SheetsController()
        self.hc = HomePageController()

    @route('/driver-check-in')
    def check_in(self):
        self.sc.check_roles_and_route(['Administrator', 'Driver'])
        requests = db.get_requests()
        active_requests = db.number_active_requests()['waitlist-num']
        driver_select = session['DRIVER-SELECT']
        return render_template('driver_check_in/driver_check_in.html', **locals())

    # Loads in the selected driver view
    @route('/driver-view', methods=['GET', 'POST'])
    def load_driver_view(self):
        json_data = request.get_json()
        load = ''
        session['DRIVER-SELECT'] = json_data['view']
        if json_data['view'] == 'Location Check In':
            load = 'locations'
            locations = db.get_db_locations()
            last_location = db.get_last_location()['location']
            next_check_in = self.hc.grab_current_route()
            next_location = next_check_in['location']
            next_time = next_check_in['time']
            if next_location == 'No more stops today' or next_location == 'No stops on the weekend':
                next_location = 'North'
            current_break_status = db.break_status()
            return render_template('driver_check_in/load_driver_check_locations.html', **locals())
        if json_data['view'] == 'Active Requests':
            load = 'requests'
            requests = db.get_requests()
            active_requests = db.number_active_requests()['waitlist-num']
            current_break_status = db.break_status()
            return render_template('driver_check_in/load_driver_check_requests.html', **locals())

    @route('/load-request', methods=['POST'])
    def load_request(self):
        json_data = request.get_json()
        username = json_data['username']
        return render_template('driver_check_in/requests_modal.html', **locals())

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

    @route('/delete-request', methods=['GET', 'POST'])
    def delete_request(self):
        json_data = request.get_json()
        username = json_data['username']
        results = db.driver_deleted_request(username)
        if results == 'success':
            self.sc.set_alert('success', 'The request has been deleted')
        else:
            self.sc.set_alert('danger', 'Something went wrong. Please call the ITS Help '
                                        'Desk at 651-638-6500 for support')
        return results

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
