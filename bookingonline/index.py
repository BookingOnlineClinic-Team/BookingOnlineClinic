"""
Nơi DUY NHẤT được phép khai báo route. Không query DB trực tiếp ở đây — mọi
thao tác DB phải đi qua bookingonline.models.dao (theo CLAUDE.md).
"""
from datetime import date, datetime, timedelta
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


@app.route('/health-profiles', methods=['GET', 'POST'])
@login_required
def health_profiles():
    """UC: Xem danh sách + tạo hồ sơ khám của người dùng đang đăng nhập
    (bao gồm cả hồ sơ đặt hộ, vd đặt cho con).
    GET  = xem danh sách. POST = tạo hồ sơ mới (chỉ role PATIENT)."""
    if request.method == 'POST':
        if current_user.role != UserRoleEnum.PATIENT:
            flash('Chỉ tài khoản bệnh nhân mới được tạo hồ sơ khám.')
            return redirect(url_for('health_profiles'))

        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        gender_raw = request.form.get('gender', '').strip()
        dob_raw = request.form.get('dateOfBirth', '').strip()
        address = request.form.get('address', '').strip()

        errors = []
        if not name:
            errors.append('Vui lòng nhập họ tên.')

        if not utils.is_valid_phone(phone):
            errors.append('Số điện thoại không hợp lệ (10 số, bắt đầu bằng 0).')

        gender = None
        if gender_raw:
            try:
                gender = GenderEnum(gender_raw)
            except ValueError:
                errors.append('Giới tính không hợp lệ.')

        date_of_birth = None
        if dob_raw:
            date_of_birth = utils.parse_date(dob_raw)
            if date_of_birth is None:
                errors.append('Ngày sinh không đúng định dạng.')
            elif date_of_birth > date.today():
                errors.append('Ngày sinh không được ở tương lai.')
            elif not utils.is_valid_birth_date(date_of_birth):
                errors.append('Ngày sinh không hợp lệ (quá xa so với hiện tại).')

        if errors:
            for e in errors:
                flash(e)
            profiles = dao.get_health_profiles_by_user(current_user.id)
            return render_template('health_profiles.html', profiles=profiles, form=request.form)

        dao.create_health_profile(
            user_id=current_user.id,
            name=name,
            phone=phone,
            gender=gender,
            date_of_birth=date_of_birth,
            address=address or None,
        )
        flash('Tạo hồ sơ khám thành công!')
        return redirect(url_for('health_profiles'))

    profiles = dao.get_health_profiles_by_user(current_user.id)
    return render_template('health_profiles.html', profiles=profiles, form=None)
