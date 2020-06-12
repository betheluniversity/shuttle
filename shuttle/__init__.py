import logging

from flask import Flask, request
from flask import session as flask_session
from datetime import datetime

import sentry_sdk

app = Flask(__name__)
app.config.from_object('config')

from shuttle.db import db_functions as db

if app.config['ENVIRON'] == 'prod' and app.config['SENTRY_URL']:
    from sentry_sdk.integrations.flask import FlaskIntegration
    sentry_sdk.init(dsn=app.config['SENTRY_URL'], integrations=[FlaskIntegration()])
    from shuttle import error

# Declaring and registering the views
from shuttle.views import View
from shuttle.schedules import SchedulesView
from shuttle.db import db_functions as db
from shuttle.shuttle_controller import ShuttleController as sc

SchedulesView.register(app)
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
    elif '/' != request.path and '/logout' not in request.path:
        print("GOT")
        if 'USERNAME' not in flask_session.keys():
            if app.config['ENVIRON'] == 'prod':
                flask_session['USERNAME'] = request.environ.get('REMOTE_USER')
            else:
                flask_session['USERNAME'] = app.config['TEST_USERNAME']
        if 'NAME' not in flask_session.keys():
            flask_session['NAME'] = db.portal_common_profile(flask_session['USERNAME'])[0]['pref_first_last_name']
        if 'USER-ROLES' not in flask_session.keys():
            try:
                flask_session['USER-ROLES'] = db.get_user_by_username(flask_session['USERNAME'])[0]
            except:
                flask_session['USER-ROLES'] = ['User']
        if 'ALERT' not in flask_session.keys():
            flask_session['ALERT'] = []
