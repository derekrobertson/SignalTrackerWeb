import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_httpauth import HTTPBasicAuth
import yaml


app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

# Import secrets
secrets = yaml.load(open(f'{basedir}\secrets.yaml'), Loader=yaml.SafeLoader)
driver = secrets['database']['driver']
username = secrets['database']['username']
password = secrets['database']['password']
fqdn = secrets['database']['fqdn']
port = secrets['database']['port']
dbname = secrets['database']['dbname']

# Get the trusted api key that the REST API uses to validate calls are coming from the SignalTracker mobile app
app.api_key = secrets['api_key']

# Configure the SQLAlchemy part of the app instance
app.config['SQLALCHEMY_ECHO'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = f"{driver}://{username}:{password}@{fqdn}:{port}/{dbname}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# Create the SQLAlchemy db instance
db = SQLAlchemy(app)
migrate = Migrate(app, db)
auth = HTTPBasicAuth()

from app import web_routes, api_routes, models