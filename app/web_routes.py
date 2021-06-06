from flask import render_template, request, abort, url_for
from flask.json import jsonify
from app import app, db
from app.models import User, Device, Reading, CellTower


@app.route('/')
@app.route('/index')
def index():
    user = {'username': 'Derek'}
    return render_template('index.html', title='Home', user=user)

