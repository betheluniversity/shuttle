from flask import render_template, make_response, redirect
from flask import session as flask_session
from flask_classy import FlaskView, route
from shuttle.schedules import SchedulesView

from shuttle import app


class View(FlaskView):
    def __init__(self):
        self.sv = SchedulesView()

    def index(self):
        route_data = self.sv.grab_current_route()
        check_in_data = self.sv.grab_check_in_driver_data()
        return render_template('index.html', **locals())

    @route('/clear')
    def clear_session(self):
        flask_session.clear()
        return 'success'

    @route('/logout', methods=['GET'])
    def logout(self):
        flask_session.clear()
        resp = make_response(redirect(app.config['LOGOUT_URL']))
        resp.set_cookie('MOD_AUTH_CAS_S', '', expires=0, path='/')
        resp.set_cookie('MOD_AUTH_CAS', '', expires=0, path='/')
        return resp