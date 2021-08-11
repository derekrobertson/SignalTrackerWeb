import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_httpauth import HTTPBasicAuth
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
import yaml


app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

# Import secrets
secrets_file = os.path.join(basedir, 'secrets.yaml')
secrets = yaml.load(open(secrets_file), Loader=yaml.SafeLoader)
driver = secrets['database']['driver']
username = secrets['database']['username']
password = secrets['database']['password']
fqdn = secrets['database']['fqdn']
port = secrets['database']['port']
dbname = secrets['database']['dbname']

# Get the SECRET_KEY we will use for flask-wtf to prevent CSRF attaches
app.config['SECRET_KEY'] = secrets['secret_key']

# Get the trusted api key that the REST API uses to validate calls are coming from the SignalTracker mobile app
app.config['API_KEY'] = secrets['api_key']

# Get the google maps api key
app.config['MAPS_API_KEY'] = secrets['maps_api_key']  

# Get the opencell id api key
app.config['OPENCELLID_API_KEY'] = secrets['opencellid_api_key']

# Configure the SQLAlchemy part of the app instance
app.config['SQLALCHEMY_ECHO'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = f"{driver}://{username}:{password}@{fqdn}:{port}/{dbname}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# Create the SQLAlchemy db instance
db = SQLAlchemy(app)
migrate = Migrate(app, db)
auth = HTTPBasicAuth()
login = LoginManager(app)
login.login_view = 'login'
bootstrap = Bootstrap(app)

from app import web_routes, api_routes, models

