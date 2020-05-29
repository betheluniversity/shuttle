from flask import render_template, make_response, redirect
from flask import session as flask_session
from flask_classy import FlaskView, route

from shuttle import app


class View(FlaskView):
    def index(self):
        return render_template('index.html')

    @route('/shuttle-stats')
    def stats(self):
        return render_template('shuttle_stats/shuttle_stats.html')

    @route('/logout', methods=['GET'])
    def logout(self):
        flask_session.clear()
        resp = make_response(redirect(app.config['LOGOUT_URL']))
        resp.set_cookie('MOD_AUTH_CAS_S', '', expires=0, path='/')
        resp.set_cookie('MOD_AUTH_CAS', '', expires=0, path='/')
        return resp