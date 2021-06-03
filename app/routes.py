from flask import render_template, request, abort, url_for
from flask.json import jsonify
from app import app, db
from app.models import User, Device, Reading, CellTower


@app.route('/')
@app.route('/index')
def index():
    user = {'username': 'Derek'}
    return render_template('index.html', title='Home', user=user)



#######################
### REST API ROUTES ###
#######################


### USERS ###



"""
USERS > GET(ALL)
"""
@app.route('/api/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([u.serialize() for u in users])



"""
USERS > GET(ID)
"""
@app.route('/api/users/<int:id>', methods=['GET'])
def get_user(id):
    user = User.query.get(id)
    if not user:
        abort(404)
    return jsonify(user.serialize())


"""
USERS > CREATE
"""
@app.route('/api/users', methods = ['POST'])
def new_user():
    first_name = request.json.get('first_name')
    last_name = request.json.get('last_name')
    email = request.json.get('email')
    password = request.json.get('password')
    if first_name is None or last_name is None or email is None or password is None:
        abort(400)  # missing args
    if User.query.filter_by(email = email).one_or_none() is not None:
        abort(409)  # existing user
    user = User(first_name = first_name, 
                last_name = last_name,
                email = email)
    user.hash_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify(user.serialize()), 201, {'Location': url_for('get_user', id = user.user_id, _external = True)}


"""
USERS > UPDATE(ID)
"""
@app.route('/api/users/<int:id>', methods=['PUT'])
def update_user(id):
    first_name = request.json.get('first_name')
    last_name = request.json.get('last_name')
    email = request.json.get('email')
    password = request.json.get('password')
    
    if first_name is None and last_name is None and email is None and password is None:
        abort(400)  # missing args
    user = User.query.get(id)
    if not user:
        abort(404)  # doesn't exist
    
    if first_name is not None:
        user.first_name = first_name
    if last_name is not None:
        user.last_name = last_name
    if email is not None:
        user.email = email
    if password is not None:
        user.hash_password(password)

    db.session.commit()
    return jsonify(user.serialize())


"""
USERS > DELETE(ID)
"""
@app.route('/api/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = User.query.get(id)
    if not user:
        abort(404)      #doesn't exist
    db.session.delete(user)
    db.session.commit()
    return jsonify({}), 204



### DEVICES ###



"""
DEVICES > GET(ALL)
"""
@app.route('/api/devices', methods=['GET'])
def get_devices():
    devices = Device.query.all()
    return jsonify([d.serialize() for d in devices])



"""
DEVICES > GET(ID)
"""
@app.route('/api/devices/<int:id>', methods=['GET'])
def get_device(id):
    device = Device.query.get(id)
    if not device:
        abort(404)
    return jsonify(device.serialize())


"""
DEVICES > CREATE
"""
@app.route('/api/devices', methods = ['POST'])
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
@app.route('/api/devices/<int:id>', methods=['PUT'])
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
@app.route('/api/devices/<int:id>', methods=['DELETE'])
def delete_device(id):
    device = Device.query.get(id)
    if not device:
        abort(404)
    db.session.delete(device)
    db.session.commit()
    return jsonify({}), 204




### READINGS ###


"""
READINGS > GET(ALL)
"""
@app.route('/api/readings', methods=['GET'])
def get_readings():
    readings = Reading.query.all()
    return jsonify([r.serialize() for r in readings])



"""
READINGS > GET(ID)
"""
@app.route('/api/readings/<int:id>', methods=['GET'])
def get_reading(id):
    reading = Reading.query.get(id)
    if not reading:
        abort(404)
    return jsonify(reading.serialize())


"""
READINGS > CREATE
"""
@app.route('/api/readings', methods = ['POST'])
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
        abort(404)   # specified device_id does not exist

    celltower = CellTower.query.get(celltower_id)
    if not celltower:
        abort(404)   # specified celltower_id does not exist

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
@app.route('/api/readings/<int:id>', methods=['PUT'])
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
@app.route('/api/readings/<int:id>', methods=['DELETE'])
def delete_reading(id):
    reading = Reading.query.get(id)
    if not reading:
        abort(404)
    db.session.delete(reading)
    db.session.commit()
    return jsonify({}), 204

    