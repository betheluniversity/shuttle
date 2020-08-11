# Packages
import re
import time
from datetime import datetime

from flask import render_template, session
from flask_classy import FlaskView, route, request

# Local
from shuttle.db import db_functions as db
from shuttle.schedules.google_sheets_controller import SheetsController
from shuttle.schedules.shuttle_schedules_controller import ScheduleController
from shuttle.shuttle_controller import ShuttleController


class RequestShuttleView(FlaskView):
    route_base = '/requests'

    def __init__(self):
        self.sc = ShuttleController()
        self.ssc = ScheduleController()
        self.shc = SheetsController()

    @route('/request-shuttle')
    def request(self):
        self.sc.check_roles_and_route(['Administrator', 'Driver', 'User'])
        locations = self.shc.grab_locations()
        active_requests = db.number_active_requests()
        if active_requests['requested-pick-up']:
            position_in_waitlist = db.get_position_in_waitlist()[0]['rownumber']

        now = datetime.now()
        current_time = now.strftime('%H:%M')
        current_time = time.strptime(current_time, '%H:%M')
        day = now.strftime('%a')
        shuttle_requestable = True
        # If it is the weekend, the hours for an On Call shuttle are only from 12:30am to 9:00pm
        if day == 'Sat' or day == 'Sun':
            if current_time < time.strptime('12:30', '%H:%M') or current_time > time.strptime('21:00', '%H:%M'):
                shuttle_requestable = False
        # If it is a weekday, the hours of operation are specific
        else:
            if current_time < time.strptime('8:00', '%H:%M') \
                    or time.strptime('9:00', '%H:%M') < current_time < time.strptime('9:45', '%H:%M') \
                    or time.strptime('10:45', '%H:%M') < current_time < time.strptime('13:00', '%H:%M') \
                    or time.strptime('13:45', '%H:%M') < current_time < time.strptime('14:30', '%H:%M') \
                    or current_time > time.strptime('21:00', '%H:%M'):
                shuttle_requestable = False
        username = session['USERNAME']
        phone_number = db.check_for_number(username)
        if phone_number:
            phone_number = phone_number[0]['phone_number']
        return render_template('request_shuttle/request_shuttle.html', **locals())

    @route('/send-request', methods=['GET', 'POST'])
    def send_shuttle_request_path(self):
        self.sc.check_roles_and_route(['Administrator', 'Driver', 'User'])
        json_data = request.get_json()
        phone_number = json_data['phone-number']
        if phone_number:
            if not re.search("^[0-9]{3}-[0-9]{3}-[0-9]{4}$", phone_number):
                self.sc.set_alert('danger', 'Please keep phone number in format 123-123-1234')
                return 'failed'
            send_number = db.send_phone_number(phone_number)
            if send_number == 'Error':
                self.sc.set_alert('danger', 'Something went wrong. Please call the ITS Help '
                                            'Desk at 651-638-6500 for support')
                return send_number
        response = db.commit_shuttle_request(json_data['pick-up-location'], json_data['drop-off-location'])
        if response == 'success':
            self.sc.set_alert('success', 'Your request has been submitted')
        elif response == 'same location':
            self.sc.set_alert('danger', 'Please select two different locations')
        elif response == 'no location':
            self.sc.set_alert('danger', 'Please select a location')
        elif response == 'bad time':
            self.sc.set_alert('danger', 'You cannot request a shuttle at this time. Refer to the On Call Shuttle '
                                        'Information below to see when the On Call Shuttle is available')
        elif response == 'bad location':
            self.sc.set_alert('danger', 'You can only request off campus locations at this time. Refer to the On Call '
                                        'Shuttle Information below to see when the On Call Shuttle is available ')
        else:
            self.sc.set_alert('danger', 'Something went wrong. Please call the ITS Help '
                                        'Desk at 651-638-6500 for support')
        return response

    @route('/delete-request')
    def delete_request(self):
        self.sc.check_roles_and_route(['Administrator', 'Driver', 'User'])
        request_to_delete = db.user_deleted_request()
        if request_to_delete == 'success':
            self.sc.set_alert('success', 'Your request has been deleted')
        else:
            self.sc.set_alert('danger', 'Something went wrong. Please try again or '
                                        'call the ITS Help Desk at 651-638-6500')
        return request_to_delete

    @route('/delete-number')
    def delete_number(self):
        self.sc.check_roles_and_route(['Administrator', 'Driver', 'User'])
        request_to_delete = db.delete_number()
        if request_to_delete == 'success':
            self.sc.set_alert('success', 'Your number has been deleted')
        else:
            self.sc.set_alert('danger', 'Something went wrong. Please try again or '
                                        'call the ITS Help Desk at 651-638-6500')
        return request_to_delete
