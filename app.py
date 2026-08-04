import os 
from flask import Flask
from dotenv import load_dotenv
from database import db
from flask_login import LoginManager

load_dotenv()

def create_app():
    app = Flask(__name__)

    #Config
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///compnote.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload

    #Database
    db.init_app(app)
    