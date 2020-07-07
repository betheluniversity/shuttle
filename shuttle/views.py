from flask import render_template, make_response, redirect
from flask import session as flask_session
from flask_classy import FlaskView, route
from shuttle import app
from shuttle.shuttle_controller import ShuttleController


class View(FlaskView):
    def __init__(self):
        self.sc = ShuttleController()

    @route('/')
    def index(self):
        check_in_data = self.sc.grab_check_in_driver_data()
        route_data = self.sc.grab_current_route()
        return render_template('homepage/index.html', **locals())

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
