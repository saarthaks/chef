from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
import pickle

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'pantry.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
db = SQLAlchemy(app)

from app import app, db

with app.app_context():
    db.create_all()

from app import routes
