from app import db
from datetime import datetime
from passlib.apps import custom_app_context as pwd_context



# SQLAlchemy models

class User(db.Model):
    __tablename__ = 'user'
    user_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(32), nullable=False)
    last_name = db.Column(db.String(32), nullable=False)
    email = db.Column(db.String(32), index=True, unique=True, nullable=False)
    pwd_hash = db.Column(db.String(128), nullable=False)
    login_failure_count = db.Column(db.Integer, default=0)
    login_locked_timestamp = db.Column(db.DateTime, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    devices = db.relationship(
        'Device',
        backref='user',
        cascade='all, delete, delete-orphan',
        single_parent=True,
        order_by='desc(Device.timestamp)'
    )

    def hash_password(self, password):
        self.pwd_hash = pwd_context.encrypt(password)


    def verify_password(self, password):
        return pwd_context.verify(password, self.pwd_hash)


    def serialize(self):
        return {
            'user_id': self.user_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'login_failure_count': self.login_failure_count,
            'login_locked_timestamp': self.login_locked_timestamp,
            'timestamp': str(datetime.fromisoformat(str(self.timestamp)))
        }

    def __repr__(self):
        return '<User {}>'.format(self.user_id)




class Device(db.Model):
    __tablename__ = 'device'
    device_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    manufacturer = db.Column(db.String(32), nullable=False)
    model = db.Column(db.String(32), nullable=False)
    serial_no = db.Column(db.String(64), nullable=False)
    android_version = db.Column(db.String(32), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    readings = db.relationship(
        'Reading',
        backref='device',
        cascade='all, delete, delete-orphan',
        single_parent=True,
        order_by='desc(Reading.timestamp)'
    )

    def serialize(self):
        return {
            'device_id': self.device_id,
            'user_id': self.user_id,
            'manufacturer': self.manufacturer,
            'model': self.model,
            'serial_no': self.serial_no,
            'android_version': self.android_version,
            'timestamp': str(datetime.fromisoformat(str(self.timestamp)))
        }

    def __repr__(self):
        return '<Device {}'.format(self.device_id)



class Reading(db.Model):
    __tablename__ = 'reading'
    reading_id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('device.device_id'))
    celltower_id = db.Column(db.Integer, db.ForeignKey('celltower.celltower_id'))
    latitude = db.Column(db.Numeric, nullable=False)
    longitude = db.Column(db.Numeric, nullable=False)
    signal_type = db.Column(db.String(8), nullable=False)
    signal_value = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def serialize(self):
        return {
            'reading_id': self.reading_id,
            'device_id': self.device_id,
            'celltower_id': self.celltower_id,
            'latitude': str(self.latitude),
            'longitude': str(self.longitude),
            'signal_type': self.signal_type,
            'signal_value': self.signal_value,
            'timestamp': str(datetime.fromisoformat(str(self.timestamp)))
        }

    def __repr__(self):
        return '<Reading {}'.format(self.reading_id)
    

class CellTower(db.Model):
    __tablename__ = 'celltower'
    celltower_id = db.Column(db.Integer, primary_key=True)
    celltower_name = db.Column(db.String(32), nullable=False)
    location_area_code = db.Column(db.String(32), nullable=False)
    mobile_country_code = db.Column(db.String(32), nullable=False)
    mobile_network_code = db.Column(db.String(32), nullable=False)
    latitude = db.Column(db.Numeric, nullable=False)
    longitude = db.Column(db.Numeric, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    readings = db.relationship(
        'Reading',
        backref='celltower',
        order_by='desc(Reading.timestamp)'
    )


    def serialize(self):
        return {
            'celltower_id': self.celltower_id,
            'celltower_name': self.celltower_name,
            'location_area_code': self.location_area_code,
            'mobile_country_code': self.mobile_country_code,
            'mobile_network_code': self.mobile_network_code,
            'latitude': str(self.latitude),
            'longitude': str(self.longitude),
            'timestamp': str(datetime.fromisoformat(str(self.timestamp)))
        }


    def __repr__(self):
        return '<CellTower {}'.format(self.celltower_id)
 