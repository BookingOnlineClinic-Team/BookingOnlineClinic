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

        data, errors = utils.validate_health_profile_form(request.form)

        if errors:
            for e in errors:
                flash(e)
            profiles = dao.get_health_profiles_by_user(current_user.id)
            return render_template('health_profiles.html', profiles=profiles, form=request.form)

        dao.create_health_profile(user_id=current_user.id, **data)
        flash('Tạo hồ sơ khám thành công!')
        return redirect(url_for('health_profiles'))

    profiles = dao.get_health_profiles_by_user(current_user.id)
    return render_template('health_profiles.html', profiles=profiles, form=None)


@app.route('/health-profiles/<int:profile_id>', methods=['GET', 'PATCH'])
@login_required
def health_profile_detail(profile_id):
    """UC: Xem/sửa 1 hồ sơ khám theo id. GET = hiển thị form sửa (chưa cần
    trang "xem chi tiết" riêng nên GET dùng luôn template form, prefill sẵn
    dữ liệu). PATCH = cập nhật thật, gọi qua fetch() trong template vì HTML
    form thuần không hỗ trợ method PATCH — trả JSON {redirect: <url>} để JS
    điều hướng sau khi xong.
    Cả 2 method đều chỉ cho chủ sở hữu (dao.get_health_profile_by_id filter
    theo current_user.id) — user khác dò id trên URL sẽ nhận 'không tìm
    thấy'/404, không lộ thông tin hồ sơ người khác."""
    profile = dao.get_health_profile_by_id(profile_id, current_user.id)

    if request.method == 'PATCH':
        if not profile:
            flash('Không tìm thấy hồ sơ khám hoặc bạn không có quyền chỉnh sửa.')
            return jsonify(redirect=url_for('health_profiles')), 404

        data, errors = utils.validate_health_profile_form(request.form)

        if errors:
            for e in errors:
                flash(e)
            return jsonify(redirect=url_for('health_profile_detail', profile_id=profile_id)), 400

        dao.update_health_profile(profile, **data)
        flash('Cập nhật hồ sơ khám thành công!')
        return jsonify(redirect=url_for('health_profiles'))

    if not profile:
        flash('Không tìm thấy hồ sơ khám hoặc bạn không có quyền chỉnh sửa.')
        return redirect(url_for('health_profiles'))
    return render_template('health_profile_edit.html', profile=profile, form=None)
