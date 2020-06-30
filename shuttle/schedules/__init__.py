from flask import render_template
from flask_classy import FlaskView, route, request
from shuttle.db import db_functions as db
import json

from shuttle.shuttle_controller import ShuttleController


class SchedulesView(FlaskView):
    def __init__(self):
        self.sc = ShuttleController()

    @route('/shuttle-stats')
    def stats(self):
        return render_template('/schedules/shuttle_stats.html')

    @route('/request-shuttle')
    def request(self):
        self.sc.check_roles_and_route(['Administrator', 'Driver', 'User'])
        return render_template('/schedules/request_shuttle.html')

    @route('/shuttle-schedules')
    def schedule(self):
        self.sc.check_roles_and_route(['Administrator'])
        return render_template('schedules/shuttle_schedules.html')

    @route('/driver-check-in')
    def check_in(self):
        self.sc.check_roles_and_route(['Administrator', 'Driver'])
        return render_template('schedules/shuttle_driver_check_in.html')

    @route('/driver-logs')
    def logs(self):
        self.sc.check_roles_and_route(['Administrator'])
        return render_template('schedules/driver_logs.html')

    @route('/users')
    def users(self):
        self.sc.check_roles_and_route(['Administrator'])
        shuttle_user = db.get_users()

        for key in shuttle_user:
            shuttle_user[key]['name'] = db.username_search(shuttle_user[key]['username'])[0]['firstName'] + \
                                        ' ' + db.username_search(shuttle_user[key]['username'])[0]['lastName']

        return render_template('/schedules/users.html', **locals())

    @route('load_user_data', methods=['POST', 'GET'])
    def load_user_data(self):
        self.sc.check_roles_and_route(['Administrator'])
        username = json.loads(request.data).get('username')
        return render_template('/schedules/user_modal.html', **locals())

    @route('delete_user', methods=['POST'])
    def delete_user(self):
        self.sc.check_roles_and_route(['Administrator'])
        username = json.loads(request.data).get('username')
        print('deleting ' + username)
        result = db.delete_user(username)
        return result


    @route('edit_user', methods=['POST'])
    def edit_user(self):
        self.sc.check_roles_and_route(['Administrator'])
        username = json.loads(request.data).get('username')
        role = json.loads(request.data).get('role')
        result = db.change_user_role(username, role)
        return result

