import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__)
app.secret_key = "dn8y130rh087hbndq0wednq018g"
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)
login = LoginManager(app=app)
login.login_view = 'login'

# Import ở CUỐI file để tránh circular import: index.py/admin.py cần app, db, login
# đã tồn tại trong module bookingonline trước khi chúng import ngược lại.
from bookingonline import index, admin
