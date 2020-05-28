from flask import session as flask_session


class ShuttleController(object):
    def __init__(self):
        pass

    # This method get's the current alert (if there is one) and then resets alert to nothing
    def get_alert(self):
        if 'ALERT' not in flask_session.keys():
            flask_session['ALERT'] = []
        alert_return = flask_session['ALERT']
        flask_session['ALERT'] = []
        return alert_return

    # This method sets the alert for when one is needed next
    def set_alert(self, message_type, message):
        flask_session['ALERT'].append({
            'type': message_type,
            'message': message
        })
        flask_session.modified = True
