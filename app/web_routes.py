from flask import render_template, flash, redirect, request, abort, url_for
from flask.json import jsonify
from app import app, db
from app.models import User, Device, Reading, CellTower
from app.forms import LoginForm
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from datetime import datetime, timedelta
from time import strftime
import requests
import json



# Default route
@app.route('/', methods=['GET', 'POST'])
@app.route('/index',  methods=['GET', 'POST'])
@login_required
def index():
    if current_user.role == 'ADMIN':
        users = User.query.filter(User.role != 'ADMIN').order_by(User.email).all()
    else:
        users = current_user

    if request.method == 'GET':
        view_date = datetime.now().strftime('%Y-%m-%d')
        view_user = current_user
        return render_template('index.html', title='SignalTracker', users=users, view_user=view_user, view_date=view_date)
        
    if request.method == 'POST':
        view_date = request.form['datepicker']
        view_user = User.query.get(request.form['selectUser'])

        # Get the users device
        device = Device.query.filter(Device.user_id == view_user.user_id).one_or_none()
        
        # Get the readings and celltowers
        view_date_plus_one_day = datetime.strptime(view_date, "%Y-%m-%d") + timedelta(days=1)
        readings = Reading.query.filter(Reading.device_id == device.device_id, 
                                    Reading.timestamp >= view_date, Reading.timestamp < str(view_date_plus_one_day)).all()

        # Get the celltowers for the readings
        celltowers = CellTower.query.filter(CellTower.celltower_id.in_([reading.celltower_id for reading in readings])).all()
        
        map_markers = []
        geolocation_url = 'http://opencellid.org/cell/get'

        for celltower in celltowers:
            query = {
                "key": app.config['OPENCELLID_API_KEY'],
                "mcc": celltower.mobile_country_code,
                "mnc": celltower.mobile_network_code,
                "lac": celltower.location_area_code,
                "cellid": celltower.celltower_name,
                "format": "json"
            }

            response = requests.get(geolocation_url, params=query)
            if response.status_code == 200:
                location = json.loads(response.text)
                map_markers.append({
                    "celltower_name": celltower.celltower_name,
                    "lat": location["lat"],
                    "lng": location["lon"]
                })

        # Google geolocate as an alternative to Opencellid
        # geolocation_url = 'https://www.googleapis.com/geolocation/v1/geolocate?key={}'.format(app.config['MAPS_API_KEY'])

        # # Get the approx GPS location of each celltower 
        # for celltower in celltowers:
        #         query = {
        #             "cellTowers": [
        #                 {
        #                     "cellId": celltower.celltower_name,
        #                     "locationAreaCode": celltower.location_area_code,
        #                     "mobileCountryCode": celltower.mobile_country_code,
        #                     "mobileNetworkCode": celltower.mobile_network_code
        #                 }
        #             ]
        #         }

        #         response = requests.post(geolocation_url, json=query)
        #         if response.status_code == 200:
        #             location = json.loads(response.text)
        #             map_markers.append({
        #                 "celltower_name": celltower.celltower_name,
        #                 "lat": location["location"]["lat"],
        #                 "lng": location["location"]["lng"]
        #             })
        

        return render_template('index.html', title='SignalTracker', users=users, view_user=view_user, view_date=view_date,
                                    device=device, readings=readings, map_markers=map_markers, maps_api_key=app.config['MAPS_API_KEY'])


# User login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).one_or_none()
        if user is None or not user.verify_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form, css_signin=True)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))