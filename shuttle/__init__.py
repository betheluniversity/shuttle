from flask import Flask, render_template

app = Flask(__name__)
app.config.from_object('config')
app.url_map.strict_slashes = False


@app.route('/')
def hello_world():
    return render_template('index.html')
