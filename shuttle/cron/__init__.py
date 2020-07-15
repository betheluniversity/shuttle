# Packages
from flask import Response, request
from flask_classy import FlaskView, route
from functools import wraps

# Local
from shuttle import app
from shuttle import db


def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == app.config['LAB_LOGIN']['username'] and password == app.config['LAB_LOGIN']['password']


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)

    return decorated


class CronView(FlaskView):
    route_base = 'cron'

    def __init__(self):
        pass

    @requires_auth
    @route('/clear-waitlist', methods=['Get'])
    def clear_waitlist(self):
        try:
            db.clear_waitlist()
            return 'success'
        except Exception as error:
            return 'failed: {0}'.format(str(error))
