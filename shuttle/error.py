import time

# Packages
from flask import render_template
from flask import session as flask_session

# Local
from shuttle import app, sentry_sdk
from sentry_sdk import configure_scope


def error_render_template(template, error, code=None):

    # Check to make sure ALERT has been set, otherwise the template will fail to load
    if 'ALERT' not in flask_session.keys():
        flask_session['ALERT'] = []

    if code != 403:  # don't log 403 errors (4/8/20)
        # Check for username - it is possible for there not to be one though so handle that as well
        username = 'no username'
        if 'USERNAME' in flask_session.keys():
            username = flask_session['USERNAME']

        with configure_scope() as scope:
            scope.set_tag("time", time.strftime("%c"))
            scope.set_tag("username", username)

        app.logger.error("{0} -- {1}".format(username, str(error)))

    return render_template(template, code=code), code


@app.errorhandler(403)
def permission_denied(e):
    return error_render_template('error/403.html', e, 403)


@app.errorhandler(404)
def page_not_found(e):
    return error_render_template('error/404.html', e, 404)


@app.errorhandler(500)
def server_error(e):
    return error_render_template('error/500.html', e, 500)


@app.errorhandler(503)
def transport_error(e):
    return error_render_template('error/503.html', e, 503)


@app.errorhandler(Exception)
def other_error(e):
    return error_render_template('error/error.html', e, 500)
