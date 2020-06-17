from flask import render_template, request
from flask_classy import FlaskView, route
from shuttle.db import db_functions as db
from shuttle.schedules.google_sheets_controller import SheetsController

from shuttle.shuttle_controller import ShuttleController


class SchedulesView(FlaskView):
    def __init__(self):
        self.sc = ShuttleController()
        self.shc = SheetsController()

    @route('/shuttle-stats')
    def stats(self):
        return render_template('/schedules/shuttle_stats.html')

    @route('/request-shuttle')
    def request(self):
        locations = self.shc.grab_locations()
        self.sc.check_roles_and_route(['Administrator', 'Driver', 'User'])
        return render_template('/schedules/request_shuttle.html', **locals())

    @route('/shuttle-schedules')
    def schedule(self):
        self.sc.check_roles_and_route(['Administrator'])
        return render_template('schedules/shuttle_schedules.html')

    @route('/driver-check-in')
    def check_in(self):
        locations = self.shc.grab_locations()
        self.sc.check_roles_and_route(['Administrator', 'Driver'])
        return render_template('schedules/shuttle_driver_check_in.html', **locals())

    @route('/driver-logs')
    def logs(self):
        self.sc.check_roles_and_route(['Administrator'])
        return render_template('schedules/driver_logs.html')

    def send_schedule_path(self):
        sent = self.shc.send_schedule()
        if sent == "success":
            self.shc.set_alert('success', 'The schedule has been submitted')
        elif sent == "no match":
            self.shc.set_alert('danger', 'Data in calendar does not match specified format')
        else:
            self.shc.set_alert('danger', 'Something went wrong. Please call the ITS Help '
                                         'Desk at 651-638-6500 for support')
        return sent

    @route('/send-schedule', methods=['GET', 'POST'])
    def send_shuttle_request_path(self):
        json_data = request.get_json()
        response = db.commit_shuttle_request(json_data['location'])
        if response == "success":
            self.shc.set_alert('success', 'Your request has been submitted')
        elif response == "bad location":
            self.shc.set_alert('danger', 'Please select a location')
        else:
            self.shc.set_alert('danger', 'Something went wrong. Please call the ITS Help '
                                         'Desk at 651-638-6500 for support')
        return response

    def check_waitlist(self):
        num_waiting = db.number_active_requests()
        return num_waiting
      
    @route('/driver-check', methods=['Get', 'POST'])
    def send_driver_check_in_info(self):
        json_data = request.get_json()
        if 'location' in json_data.keys():
            response = db.commit_driver_check_in(json_data['location'],json_data['direction'], "")
            if response == "success arrival":
                self.shc.set_alert('success', 'Your arrival has been recorded')
            elif response == "success departure":
                self.shc.set_alert('success', 'Your departure has been recorded')
        else:
            response = db.commit_driver_check_in("","",json_data['break'])
        if response == "bad location":
            self.shc.set_alert('danger', 'Please select a location')
        elif response == "Error":
            self.shc.set_alert('danger', 'Something went wrong. Please try again or '
                                         'call the ITS Help Desk at 651-638-6500')
        return response
