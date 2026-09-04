from datetime import datetime, timedelta
from flask import render_template, request, redirect, flash, url_for, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from bookingonline import app, login, db
from bookingonline.models.models import *
from bookingonline.models import dao
from bookingonline import utils

if __name__ == "__main__":
    app.run(debug=True)