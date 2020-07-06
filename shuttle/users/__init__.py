from flask import render_template, session
from flask_classy import FlaskView, route, request
from shuttle.db import db_functions as db
import json
from shuttle.schedules.google_sheets_controller import SheetsController
from shuttle.schedules.shuttle_schedules_controller import ScheduleController
from shuttle.shuttle_controller import ShuttleController


class UsersView(FlaskView):
    def __init__(self):
        self.sc = ShuttleController()
        self.ssc = ScheduleController()
        self.shc = SheetsController()

    @route('/users')
    def users(self):
        self.sc.check_roles_and_route(['Administrator'])
        shuttle_user = db.get_users()
        current_user = session['USERNAME']
        for key in shuttle_user:
            shuttle_user[key]['name'] = db.username_search(shuttle_user[key]['username'])[0]['firstName'] + \
                                        ' ' + db.username_search(shuttle_user[key]['username'])[0]['lastName']
        return render_template('users/users.html', **locals())

    @route('load_user_data', methods=['POST', 'GET'])
    def load_user_data(self):
        self.sc.check_roles_and_route(['Administrator'])
        username = json.loads(request.data).get('username')
        return render_template('users/user_modal.html', **locals())

    @route('delete_user', methods=['POST'])
    def delete_user(self):
        self.sc.check_roles_and_route(['Administrator'])
        username = json.loads(request.data).get('username')
        if username != session['USERNAME']:
            result = db.delete_user(username)
            return result
        else:
            self.sc.set_alert('danger', 'You cannot delete your own account.')
            return 'error'

    @route('edit_user', methods=['POST'])
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
