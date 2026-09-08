"""
Nơi DUY NHẤT được phép khai báo route. Không query DB trực tiếp ở đây — mọi
thao tác DB phải đi qua bookingonline.models.dao (theo CLAUDE.md).
"""
from datetime import datetime, timedelta
from flask import render_template, request, redirect, flash, url_for, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from bookingonline import app, login, db
from bookingonline.models.models import *
from bookingonline.models import dao
from bookingonline import utils


@login.user_loader
def load_user(user_id):
    return dao.get_user_by_id(user_id)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = dao.get_user_by_username(username)
        if user and utils.verify_password(password, user.password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Sai tên đăng nhập hoặc mật khẩu!')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/ho-so-kham')
@login_required
def list_health_profiles():
    """UC: Xem danh sách hồ sơ khám của người dùng đang đăng nhập
    (bao gồm cả hồ sơ đặt hộ, vd đặt cho con)."""
    profiles = dao.get_health_profiles_by_user(current_user.id)
    return render_template('health_profiles.html', profiles=profiles)
