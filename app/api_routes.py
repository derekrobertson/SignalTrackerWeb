from flask import request, abort, url_for, g
from flask.json import jsonify
from app import app, db, auth
from app.models import User, Device, Reading, CellTower
import functools


# Verification of user creds supplied in HTTPBasic authorization header
# Saves the authenticated user details in the Flask 'g' session object
@auth.verify_password
def verify_password(email, password):
    user = User.query.filter_by(email=email).one_or_none()
    if user is None or not user.verify_password(password):
        return False
    g.user = user
    return True


# Decorator function that protects any api route by ensuring 
# that a valid api key is provided in the x-api-key header
def require_api_key(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        if request.headers.get('x-api-key') != app.api_key:
            abort(403)  # forbidden
        # execute the wrapped function
        return f(*args, **kwargs)
    return wrapped


# Decorator function that protects any api route by ensuring 
# that the user has ROLE=ADMIN in the user table.
def require_admin_role(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        if g.user.role != "ADMIN":
            abort(403)  # forbidden
        # execute the wrapped function
        return f(*args, **kwargs)
    return wrapped



######################
# REST API ROUTES
######################



### USERS ###

"""
USERS > GET(ALL)
"""
@app.route('/api/v1.0/users', methods=['GET'])
@auth.login_required
@require_api_key
@require_admin_role
def get_users():
    users = User.query.all()
    return jsonify([u.serialize() for u in users])



"""
USERS > GET(ID)
"""
@app.route('/api/v1.0/users/<int:id>', methods=['GET'])
@auth.login_required
@require_api_key
def get_user(id):
    user = User.query.get(id)
    if not user:
        abort(404)
    # A non-admin level user is only permitted to retrieve their own user record
    if g.user.role != "ADMIN" and user.email != g.user.email:
        abort(403)  # forbidden
    return jsonify(user.serialize())


"""
USERS > CREATE
As the mobile app needs the ability to register a new user, the api_key value is used to 
validate the key provided by the caller to the api. If it matches it is allowed.
"""
@app.route('/api/v1.0/users', methods = ['POST'])
@require_api_key
def new_user():
    first_name = request.json.get('first_name')
    last_name = request.json.get('last_name')
    email = request.json.get('email')
    password = request.json.get('password')
    role = request.json.get('role')

    if first_name is None or last_name is None or email is None or password is None or role is None:
        abort(400)  # missing args
    if role != 'USER' and role != 'ADMIN':
        abort(400)  # bad role provided
    if User.query.filter_by(email = email).one_or_none() is not None:
        abort(409)  # existing user
    user = User(first_name = first_name, 
                last_name = last_name,
                email = email,
                role = role)
    user.hash_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify(user.serialize()), 201, {'Location': url_for('get_user', id = user.user_id, _external = True)}


"""
USERS > UPDATE(ID)
"""
@app.route('/api/v1.0/users/<int:id>', methods=['PUT'])
@auth.login_required
@require_api_key
def update_user(id):
    first_name = request.json.get('first_name')
    last_name = request.json.get('last_name')
    email = request.json.get('email')
    password = request.json.get('password')
    role = request.json.get('role')
    
    if first_name is None and last_name is None and email is None and password is None and role is None:
        abort(400)  # missing args

    user = User.query.get(id)
    if not user:
        abort(409)  # conflict

    # A non-admin level user is only permitted to retrieve their own user record
    if g.user.role != "ADMIN" and user.email != g.user.email:
        abort(403)  # forbidden
    
    if first_name is not None:
        user.first_name = first_name
    if last_name is not None:
        user.last_name = last_name
    if email is not None:
        user.email = email
    if password is not None:
        user.hash_password(password)
    if role is not None:
        if role != 'USER' and role != 'ADMIN':
            abort(400)      # bad role provided
        user.role = role

    db.session.commit()
    return jsonify(user.serialize())


"""
USERS > DELETE(ID)
"""
@app.route('/api/v1.0/users/<int:id>', methods=['DELETE'])
@auth.login_required
@require_api_key
def delete_user(id):
    user = User.query.get(id)
    if not user:
        abort(404)      #doesn't exist
    # A non-admin level user is only permitted to retrieve their own user record
    if g.user.role != "ADMIN" and user.email != g.user.email:
        abort(403)  # forbidden

    db.session.delete(user)
    db.session.commit()
    return jsonify({}), 204



### DEVICES ###



"""
DEVICES > GET(ALL)
"""
@app.route('/api/v1.0/devices', methods=['GET'])
@auth.login_required
@require_api_key
@require_admin_role
def get_devices():
    devices = Device.query.all()
    return jsonify([d.serialize() for d in devices])



"""
DEVICES > GET(ID)
"""
@app.route('/api/v1.0/devices/<int:id>', methods=['GET'])
@require_api_key
@auth.login_required
def get_device(id):
    device = Device.query.get(id)
    if not device:
        abort(404)
    # A non-admin level user is only permitted to retrieve devices that belong to that user
    if g.user.role != "ADMIN":
        user = User.query.get(device.user_id)
        if not user:
            abort(404)
        if user.email != g.user.email:
            abort(403)  # forbidden

    return jsonify(device.serialize())


"""
DEVICES > CREATE
"""
@app.route('/api/v1.0/devices', methods = ['POST'])
@auth.login_required
@require_api_key
def new_device():
    user_id = request.json.get('user_id')
    manufacturer = request.json.get('manufacturer')
    model = request.json.get('model')
    serial_no = request.json.get('serial_no')
    android_version = request.json.get('android_version')

    if user_id is None or manufacturer is None or model is None or serial_no is None or android_version is None:
        abort(400)  # missing args

    user = User.query.get(user_id)
    if not user:
        abort(404)   # specified user_id does not exist

    # A non-admin level user is only permitted to retrieve devices that belong to that user
    if g.user.role != "ADMIN" and user.email != g.user.email:
        abort(403)  # forbidden

    # Create the new device
    device = Device(user_id = user_id, 
                manufacturer = manufacturer,
                model = model,
                serial_no = serial_no,
                android_version = android_version)
    
    db.session.add(device)
    db.session.commit()

    return jsonify(device.serialize()), 201, {'Location': url_for('get_user', id = device.device_id, _external = True)}


"""
DEVICES > UPDATE(ID)
"""
@app.route('/api/v1.0/devices/<int:id>', methods=['PUT'])
@auth.login_required
@require_api_key
def update_device(id):
    manufacturer = request.json.get('manufacturer')
    model = request.json.get('model')
    serial_no = request.json.get('serial_no')
    android_version = request.json.get('android_version')

    if manufacturer is None and model is None and serial_no is None and android_version is None:
        abort(400)  # missing args

    device = Device.query.get(id)
    if not device:
        abort(404)  # device doesn't exist

    # A non-admin level user is only permitted to retrieve devices that belong to that user
    if g.user.role != "ADMIN":
        user = User.query.get(device.user_id)
        if not user:
            abort(409)
        if user.email != g.user.email:
            abort(403)  # forbidden

    if manufacturer is not None:
        device.manufacturer = manufacturer
    if model is not None:
        device.model = model
    if serial_no is not None:
        device.serial_no = serial_no
    if android_version is not None:
        device.android_version = android_version

    db.session.commit()
    return jsonify(device.serialize())


"""
DEVICES > DELETE(ID)
"""
@app.route('/api/v1.0/devices/<int:id>', methods=['DELETE'])
@auth.login_required
@require_api_key
def delete_device(id):
    device = Device.query.get(id)
    if not device:
        abort(404)

    # A non-admin level user is only permitted to retrieve devices that belong to that user
    if g.user.role != "ADMIN":
        user = User.query.get(device.user_id)
        if not user:
            abort(409)
        if user.email != g.user.email:
            abort(403)  # forbidden

    db.session.delete(device)
    db.session.commit()
    return jsonify({}), 204




### READINGS ###


"""
READINGS > GET(ALL)
"""
@app.route('/api/v1.0/readings', methods=['GET'])
@auth.login_required
@require_api_key
@require_admin_role
def get_readings():
    readings = Reading.query.all()
    return jsonify([r.serialize() for r in readings])



"""
READINGS > GET(ID)
"""
@app.route('/api/v1.0/readings/<int:id>', methods=['GET'])
@auth.login_required
@require_api_key
def get_reading(id):
    reading = Reading.query.get(id)
    if not reading:
        abort(404)

    # A non-admin level user is only permitted to retrieve readings that belong to that user
    if g.user.role != "ADMIN":
        device = Device.query.get(reading.device_id)
        if not device:
            abort(404)
        user = User.query.get(device.user_id)
        if not user:
            abort(409)
        if user.email != g.user.email:
            abort(403)  # forbidden

    return jsonify(reading.serialize())


"""
READINGS > CREATE
"""
@app.route('/api/v1.0/readings', methods = ['POST'])
@auth.login_required
@require_api_key
def new_reading():
    device_id = request.json.get('device_id')
    celltower_id = request.json.get('celltower_id')
    latitude = request.json.get('latitude')
    longitude = request.json.get('longitude')
    signal_type = request.json.get('signal_type')
    signal_value = request.json.get('signal_value')

    if device_id is None or celltower_id is None or latitude is None or longitude is None \
             or signal_type is None or signal_value is None:
        abort(400)  # missing args

    device = Device.query.get(device_id)
    if not device:
        abort(400)   # specified device_id does not exist

    celltower = CellTower.query.get(celltower_id)
    if not celltower:
        abort(400)   # specified celltower_id does not exist

    # A non-admin level user is only permitted to create readings that belong to that user
    if g.user.role != "ADMIN":
        user = User.query.get(device.user_id)
        if not user:
            abort(409)
        if user.email != g.user.email:
            abort(403)  # forbidden


    reading = Reading(device_id = device_id, 
                celltower_id = celltower_id,
                latitude = latitude,
                longitude = longitude,
                signal_type = signal_type,
                signal_value = signal_value)
    
    db.session.add(reading)
    db.session.commit()

    return jsonify(reading.serialize()), 201, {'Location': url_for('get_user', id = reading.reading_id, _external = True)}


"""
READINGS > UPDATE(ID)
"""
@app.route('/api/v1.0/readings/<int:id>', methods=['PUT'])
@auth.login_required
@require_api_key
def update_reading(id):
    latitude = request.json.get('latitude')
    longitude = request.json.get('longitude')
    signal_type = request.json.get('signal_type')
    signal_value = request.json.get('signal_value')

    if latitude is None and longitude is None and signal_type is None and signal_value is None:
        abort(400)  # missing args

    reading = Reading.query.get(id)
    if not reading:
        abort(404)  # reading doesn't exist

    # A non-admin level user is only permitted to retrieve readings that belong to that user
    if g.user.role != "ADMIN":
        device = Device.query.get(reading.device_id)
        if not device:
            abort(409)
        user = User.query.get(device.user_id)
        if not user:
            abort(409)
        if user.email != g.user.email:
            abort(403)  # forbidden

    if latitude is not None:
        reading.latitude = latitude
    if longitude is not None:
        reading.longitude = longitude
    if signal_type is not None:
        reading.signal_type = signal_type
    if signal_value is not None:
        reading.signal_value = signal_value

    db.session.commit()
    return jsonify(reading.serialize())


"""
READINGS > DELETE(ID)
"""
@app.route('/api/v1.0/readings/<int:id>', methods=['DELETE'])
@auth.login_required
@require_api_key
def delete_reading(id):
    reading = Reading.query.get(id)
    if not reading:
        abort(404)

    # A non-admin level user is only permitted to retrieve readings that belong to that user
    if g.user.role != "ADMIN":
        device = Device.query.get(reading.device_id)
        if not device:
            abort(409)  # conflict
        user = User.query.get(device.user_id)
        if not user:
            abort(409)  # conflict
        if user.email != g.user.email:
            abort(403)  # forbidden

    db.session.delete(reading)
    db.session.commit()
    return jsonify({}), 204



### CELLTOWER ###


"""
CELLTOWERS > GET(ALL)
"""
@app.route('/api/v1.0/celltowers', methods=['GET'])
@auth.login_required
@require_api_key
def get_celltowers():
    celltowers = CellTower.query.all()
    return jsonify([c.serialize() for c in celltowers])



"""
CELLTOWERS > GET(ID)
"""
@app.route('/api/v1.0/celltowers/<int:id>', methods=['GET'])
@auth.login_required
@require_api_key
def get_celltower(id):
    celltower = CellTower.query.get(id)
    if not celltower:
        abort(404)
    return jsonify(celltower.serialize())


"""
CELLTOWERS > CREATE
"""
@app.route('/api/v1.0/celltowers', methods = ['POST'])
@auth.login_required
@require_api_key
def new_celltower():
    celltower_name = request.json.get('celltower_name')
    location_area_code = request.json.get('location_area_code')
    mobile_country_code = request.json.get('mobile_country_code')
    mobile_network_code = request.json.get('mobile_network_code')
    latitude = request.json.get('latitude')
    longitude = request.json.get('longitude')

    if celltower_name is None or location_area_code is None or mobile_country_code is None or mobile_network_code is None \
             or latitude is None or longitude is None:
        abort(400)  # missing args

    if CellTower.query.filter_by(celltower_name = celltower_name).one_or_none() is not None:
        abort(409)  # existing celltower

    celltower = CellTower(celltower_name = celltower_name, 
                location_area_code = location_area_code,
                mobile_country_code = mobile_country_code,
                mobile_network_code = mobile_network_code,
                latitude = latitude,
                longitude = longitude)
    
    db.session.add(celltower)
    db.session.commit()

    return jsonify(celltower.serialize()), 201, {'Location': url_for('get_celltower', id = celltower.celltower_id, _external = True)}


"""
CELLTOWERS > UPDATE(ID)
"""
@app.route('/api/v1.0/celltowers/<int:id>', methods=['PUT'])
@auth.login_required
@require_api_key
@require_admin_role
def update_celltower(id):
    celltower_name = request.json.get('celltower_name')
    location_area_code = request.json.get('location_area_code')
    mobile_country_code = request.json.get('mobile_country_code')
    latitude = request.json.get('latitude')
    longitude = request.json.get('longitude')

    if celltower_name is None and location_area_code is None and mobile_country_code is None \
                            and latitude is None and longitude is None:
        abort(400)  # missing args

    celltower = CellTower.query.get(id)
    if not celltower:
        abort(404)  # reading doesn't exist

    if celltower_name is not None:
        celltower.celltower_name = celltower_name
    if location_area_code is not None:
        celltower.location_area_code = location_area_code
    if mobile_country_code is not None:
        celltower.mobile_country_code = mobile_country_code
    if latitude is not None:
        celltower.latitude = latitude
    if longitude is not None:
        celltower.longitude = longitude

    db.session.commit()
    return jsonify(celltower.serialize())


"""
CELLTOWERS > DELETE(ID)
"""
@app.route('/api/v1.0/celltowers/<int:id>', methods=['DELETE'])
@auth.login_required
@require_api_key
@require_admin_role
def delete_celltower(id):
    celltower = CellTower.query.get(id)
    if not celltower:
        abort(404)
    db.session.delete(celltower)
    db.session.commit()
    return jsonify({}), 204
