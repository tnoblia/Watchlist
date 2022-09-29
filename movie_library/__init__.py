from distutils.command.config import config
from re import A
from dotenv import load_dotenv
from flask import Flask
from pymongo import MongoClient
from movie_library.routes import pages 
import os

#<title>{{title| dafault('Movie watchlist')}}</title>
load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config["MONGODB_URI"] = os.environ.get("MONGODB_URI")
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "d1f0b03b1470440e90246c0ee76a36a7")
    app.db = MongoClient(app.config["MONGODB_URI"]).get_default_database()
    app.register_blueprint(pages)
    return app

