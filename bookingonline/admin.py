
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