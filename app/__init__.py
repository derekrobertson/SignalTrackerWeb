import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import yaml


app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

# Import secrets
secrets = yaml.load(open(f'{basedir}\secrets.yaml'))
driver = secrets['database']['driver']
username = secrets['database']['username']
password = secrets['database']['password']
fqdn = secrets['database']['fqdn']
port = secrets['database']['port']
dbname = secrets['database']['dbname']

# Configure the SQLAlchemy part of the app instance
app.config['SQLALCHEMY_ECHO'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = f"{driver}://{username}:{password}@{fqdn}:{port}/{dbname}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# Create the SQLAlchemy db instance
db = SQLAlchemy(app)
migrate = Migrate(app, db)
    

from app import routes, api_routes, models