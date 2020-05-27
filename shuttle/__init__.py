from flask import Flask, render_template

import sentry_sdk


app = Flask(__name__)
app.config.from_object('config')

if app.config['ENVIRON'] == 'prod' and app.config['SENTRY_URL']:
    from sentry_sdk.integrations.flask import FlaskIntegration
    sentry_sdk.init(dsn=app.config['SENTRY_URL'], integrations=[FlaskIntegration()])


@app.route('/')
def hello_world():
    return render_template('index.html')
