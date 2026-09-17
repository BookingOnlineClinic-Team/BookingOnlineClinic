
# Admin - Cấu hình hệ thống
# Module này theo cùng phong cách với index.py: định nghĩa route trực tiếp
# trên `app` dùng chung của project (không dùng Flask Blueprint, vì phần còn
# lại của codebase cũng không dùng blueprint). Để các route ở đây được đăng
# ký, index.py (module thực sự chạy `app.run()`) phải import module này -
# xem dòng `import bookingonline.admin` đã thêm ở đầu index.py.

from functools import wraps
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from bookingonline import app
from bookingonline.models import dao
from bookingonline.models.models import UserRoleEnum
import utils


def admin_required(view_func):
    #Chỉ cho phép tài khoản role ADMIN truy cập. Luôn dùng kèm @login_required
    #(đặt @login_required phía dưới, chạy trước) để current_user chắc chắn tồn tại.
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if current_user.role != UserRoleEnum.ADMIN:
            flash("Bạn không có quyền truy cập trang này.", "error")
            return redirect(url_for("index"))
        return view_func(*args, **kwargs)
    return wrapper


@app.route("/admin/settings", methods=["GET", "POST"])
@login_required
@admin_required
def admin_settings():
    config = dao.get_system_config()

    if request.method == "POST":
        data, errors = utils.validate_system_config_form(request.form)
        if errors:
            for e in errors:
                flash(e, "error")
            return redirect(url_for("admin_settings"))

        dao.update_system_config(config, **data)
        flash("Đã lưu cấu hình hệ thống thành công.", "success")
        return redirect(url_for("admin_settings"))

    return render_template(
        "admin_settings.html",
        active_page="admin-settings",
        config=config,
        selected_days=set(config.workingDaysList()),
    )

# bichnhu - admin - quan ly chuyen khoa
@app.route("/admin/specializations", methods=["GET", "POST"])
@login_required
@admin_required
def admin_specializations():
    if request.method == "POST":
        data, errors = utils.validate_specialization_form(request.form)
        if errors:
            for e in errors:
                flash(e, "error")
            return redirect(url_for("admin_specializations"))

        dao.create_specialization(**data)
        flash("Đã thêm chuyên khoa mới.", "success")
        return redirect(url_for("admin_specializations"))

    specializations = dao.get_all_specializations(active_only=False)
    spec_rows = [
        {
            "spec": s,
            "doctor_count": dao.count_doctors_in_specialization(s.id),
        }
        for s in specializations
    ]
    return render_template(
        "admin_specializations.html",
        active_page="admin-specializations",
        spec_rows=spec_rows,
    )


@app.route("/admin/specializations/<int:specialization_id>/edit", methods=["POST"])
@login_required
@admin_required
def admin_specialization_edit(specialization_id):
    spec = dao.get_specialization_by_id(specialization_id)
    if not spec:
        flash("Không tìm thấy chuyên khoa.", "error")
        return redirect(url_for("admin_specializations"))

    data, errors = utils.validate_specialization_form(request.form, exclude_id=spec.id)
    if errors:
        for e in errors:
            flash(e, "error")
        return redirect(url_for("admin_specializations"))

    dao.update_specialization(spec, **data)
    flash("Đã cập nhật chuyên khoa.", "success")
    return redirect(url_for("admin_specializations"))


@app.route("/admin/specializations/<int:specialization_id>/toggle-active", methods=["POST"])
@login_required
@admin_required
def admin_specialization_toggle_active(specialization_id):
    spec = dao.get_specialization_by_id(specialization_id)
    if not spec:
        flash("Không tìm thấy chuyên khoa.", "error")
        return redirect(url_for("admin_specializations"))

    dao.toggle_specialization_active(spec)
    flash(f"Đã {'mở khóa' if spec.active else 'khóa'} chuyên khoa \"{spec.name}\".", "success")
    return redirect(url_for("admin_specializations"))


@app.route("/admin/specializations/<int:specialization_id>/delete", methods=["POST"])
@login_required
@admin_required
def admin_specialization_delete(specialization_id):
    spec = dao.get_specialization_by_id(specialization_id)
    if not spec:
        flash("Không tìm thấy chuyên khoa.", "error")
        return redirect(url_for("admin_specializations"))

    ok, error_msg = dao.delete_specialization(spec)
    if not ok:
        flash(error_msg, "error")
    else:
        flash("Đã xóa chuyên khoa.", "success")
    return redirect(url_for("admin_specializations"))


# bichnhu - admin - quản lý bác sĩ (tạo tài khoản + hồ sơ bác sĩ)


@app.route("/admin/doctors", methods=["GET", "POST"])
@login_required
@admin_required
def admin_doctors():
    if request.method == "POST":
        # POST ở trang danh sách = TẠO MỚI bác sĩ (kèm tài khoản đăng nhập)
        data, errors = utils.validate_doctor_account_form(request.form, is_edit=False)
        if errors:
            for e in errors:
                flash(e, "error")
            return redirect(url_for("admin_doctors"))

        dao.create_doctor_account(
            name=data["name"], username=data["username"], password=data["password"],
            email=data["email"], specialization_id=data["specialization_id"],
            license_number=data["license_number"], experience_yrs=data["experience_yrs"],
            fee=data["fee"], phone=data["phone"], gender=data["gender"],
            description=data["description"], bio=data["bio"], avatar_url=data["avatar_url"],
        )
        flash(f"Đã tạo tài khoản bác sĩ \"{data['name']}\" thành công.", "success")
        return redirect(url_for("admin_doctors"))

    doctors = dao.get_all_doctors_admin()
    specializations = dao.get_all_specializations(active_only=False)
    return render_template(
        "admin_doctors.html",
        active_page="admin-doctors",
        doctors=doctors,
        specializations=specializations,
    )


@app.route("/admin/doctors/<int:doctor_id>/edit", methods=["POST"])
@login_required
@admin_required
def admin_doctor_edit(doctor_id):
    doctor = dao.get_doctor_by_id(doctor_id)
    if not doctor:
        flash("Không tìm thấy bác sĩ.", "error")
        return redirect(url_for("admin_doctors"))

    data, errors = utils.validate_doctor_account_form(request.form, is_edit=True)
    if errors:
        for e in errors:
            flash(e, "error")
        return redirect(url_for("admin_doctors"))

    dao.update_doctor_account(
        doctor, name=data["name"], email=data["email"],
        specialization_id=data["specialization_id"],
        license_number=data["license_number"], experience_yrs=data["experience_yrs"],
        fee=data["fee"], phone=data["phone"], gender=data["gender"],
        description=data["description"], bio=data["bio"], avatar_url=data["avatar_url"],
    )
    flash("Đã cập nhật thông tin bác sĩ.", "success")
    return redirect(url_for("admin_doctors"))


@app.route("/admin/doctors/<int:doctor_id>/toggle-active", methods=["POST"])
@login_required
@admin_required
def admin_doctor_toggle_active(doctor_id):
    # Khóa/Mở khóa tài khoản đăng nhập của bác sĩ (không xóa dữ liệu)
    doctor = dao.get_doctor_by_id(doctor_id)
    if not doctor:
        flash("Không tìm thấy bác sĩ.", "error")
        return redirect(url_for("admin_doctors"))

    dao.toggle_doctor_active(doctor)
    flash(f"Đã {'mở khóa' if doctor.user.active else 'khóa'} tài khoản bác sĩ \"{doctor.user.name}\".", "success")
    return redirect(url_for("admin_doctors"))


@app.route("/admin/doctors/<int:doctor_id>/reset-password", methods=["POST"])
@login_required
@admin_required
def admin_doctor_reset_password(doctor_id):
    # Admin đặt lại mật khẩu mới cho bác sĩ (khi bác sĩ quên mật khẩu)
    doctor = dao.get_doctor_by_id(doctor_id)
    if not doctor:
        flash("Không tìm thấy bác sĩ.", "error")
        return redirect(url_for("admin_doctors"))

    new_password = request.form.get("newPassword", "").strip()
    if not new_password or len(new_password) < 6:
        flash("Mật khẩu mới phải có tối thiểu 6 ký tự.", "error")
        return redirect(url_for("admin_doctors"))

    dao.reset_doctor_password(doctor, new_password)
    flash(f"Đã đặt lại mật khẩu cho bác sĩ \"{doctor.user.name}\".", "success")
    return redirect(url_for("admin_doctors"))