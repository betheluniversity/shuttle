import logging

from flask import Flask, request
from flask import session as flask_session
from datetime import datetime

import sentry_sdk


app = Flask(__name__)
app.config.from_object('config')

if app.config['ENVIRON'] == 'prod' and app.config['SENTRY_URL']:
    from sentry_sdk.integrations.flask import FlaskIntegration
    sentry_sdk.init(dsn=app.config['SENTRY_URL'], integrations=[FlaskIntegration()])
    from shuttle import error

# Declaring and registering the views
from shuttle.views import View
from shuttle.shuttle_controller import ShuttleController as sc

View.register(app)


# This makes these variables open to use everywhere
@app.context_processor
def utility_processor():
    to_return = {}
    to_return.update({
        'now': datetime.now(),
        'alert': sc().get_alert(),
    })

    return to_return


@app.before_request
def before_request():
    if '/static/' in request.path \
            or '/assets/' in request.path \
            or '/cron/' in request.path \
            or '/no-cas/' in request.path:

        if 'ALERT' not in flask_session.keys():
            flask_session['ALERT'] = []
    else:
        if 'ALERT' not in flask_session.keys():
            flask_session['ALERT'] = []