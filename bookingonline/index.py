from datetime import datetime, timedelta
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from bookingonline import app, db, login_manager
from bookingonline.models import dao
import utils
from bookingonline.models.models import ( User, GenderEnum, UserRoleEnum, PaymentStatusEnum, Appointment,)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.context_processor
def inject_globals():
    unread_count = 0
    if current_user.is_authenticated:
        unread_count = dao.get_unread_notification_count(current_user.id)
    return dict(unread_notification_count=unread_count)

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        if current_user.role == UserRoleEnum.DOCTOR:
            return redirect(url_for("doctor_profile_detail"))
        return redirect(url_for("select_profile"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = dao.verify_login(username, password)
        if user:
            login_user(user)
            flash("Đăng nhập thành công!", "success")
            if user.role == UserRoleEnum.DOCTOR:
                return redirect(url_for("doctor_profile_detail"))
            return redirect(url_for("select_profile"))
        flash("Sai tên đăng nhập hoặc mật khẩu.", "error")
    return render_template("login.html", active_page="login")


@app.route("/logout")
def logout():
    logout_user()
    flash("Đã đăng xuất.", "info")
    return redirect(url_for("login"))

@app.route("/")
def index():
    specializations = dao.get_all_specializations()
    services = [
        {"icon": s.icon, "name": s.name, "desc": s.description or "Khám và tư vấn chuyên khoa cùng đội ngũ bác sĩ giàu kinh nghiệm."}
        for s in specializations[:4]
    ]
    all_doctors = []
    for s in specializations:
        all_doctors.extend(dao.get_doctors_by_specialization(s.id))
    doctors = [
        {
            "id": d.id,
            "name": d.user.name if d.user else "Bác sĩ",
            "specialization": d.specialization.name if d.specialization else "",
            "rating": d.averageRating or 4.8,
            "experience": d.experienceYrs,
            "room": d.room,
            "fee": f"{int(d.fee):,}".replace(",", ".") + " ₫",
        }
        for d in all_doctors[:6]
    ]
    return render_template("index.html", active_page="landing", services=services, doctors=doctors)

@app.route("/select-profile", methods=["GET", "POST"])
@login_required
def select_profile():
    my_profiles = dao.get_patient_profiles_by_owner(current_user.id)
    if request.method == "POST":
        phone = request.form.get("phone", "").strip()
        name = request.form.get("name", "").strip()
        profile = dao.search_patient_profile(phone, name)
        if not profile:
            flash("Không tìm thấy hồ sơ theo số điện thoại và họ tên đã nhập, vui lòng nhập lại hoặc tạo hồ sơ mới.", "warning")
            return redirect(url_for("select_profile"))
        return redirect(url_for("select_specialization", profile_id=profile.id))
    return render_template(
        "appointment_profile_select.html",
        active_page="profile",
        profiles=my_profiles,
    )

@app.route("/new-profile", methods=["GET", "POST"])
@login_required
def create_profile():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        gender_raw = request.form.get("gender")
        dob_raw = request.form.get("date_of_birth")
        address = request.form.get("address", "").strip()
        if not name or not phone:
            flash("Vui lòng nhập đầy đủ họ tên và số điện thoại", "error")
            return redirect(url_for("select_profile"))
        gender = GenderEnum[gender_raw] if gender_raw in GenderEnum.__members__ else None
        date_of_birth = (datetime.strptime(dob_raw, "%Y-%m-%d").date() if dob_raw else None)
        profile = dao.create_patient_profile(
            owner=current_user,
            name=name,
            phone=phone,
            gender=gender,
            date_of_birth=date_of_birth,
            address=address,
        )
        flash("Tạo hồ sơ khám thành công.", "success")
        return redirect(url_for("select_specialization", profile_id=profile.id))
    return redirect(url_for("select_profile", open_create_modal=1))

@app.route("/patient-profiles/<int:profile_id>", methods=["GET", "PATCH"])
@login_required
def patient_profile_detail(profile_id):
    profile = dao.get_patient_profile_by_owner(profile_id, current_user.id)

    if request.method == "PATCH":
        if not profile:
            flash("Không tìm thấy hồ sơ khám hoặc bạn không có quyền chỉnh sửa.", "error")
            return jsonify(redirect=url_for("select_profile")), 404

        data, errors = utils.validate_patient_profile_form(request.form)
        if errors:
            for e in errors:
                flash(e, "error")
            return jsonify(redirect=url_for("patient_profile_detail", profile_id=profile_id)), 400

        dao.update_patient_profile(profile, **data)
        flash("Cập nhật hồ sơ khám thành công!", "success")
        return jsonify(redirect=url_for("select_profile"))

    if not profile:
        flash("Không tìm thấy hồ sơ khám hoặc bạn không có quyền chỉnh sửa.", "error")
        return redirect(url_for("select_profile"))
    return render_template("patient_profile_edit.html", active_page="profile", profile=profile)

@app.route("/doctor-profile", methods=["GET", "PATCH"])
@login_required
def doctor_profile_detail():
    if current_user.role != UserRoleEnum.DOCTOR:
        flash("Chỉ tài khoản bác sĩ mới có hồ sơ bác sĩ.", "error")
        return redirect(url_for("index"))

    profile = dao.get_doctor_profile_by_user(current_user.id)
    if not profile:
        flash("Không tìm thấy hồ sơ bác sĩ của bạn.", "error")
        return redirect(url_for("index"))

    if request.method == "PATCH":
        data, errors = utils.validate_doctor_profile_form(request.form)
        if errors:
            for e in errors:
                flash(e, "error")
            return jsonify(redirect=url_for("doctor_profile_detail")), 400

        dao.update_doctor_profile(profile, **data)
        flash("Cập nhật hồ sơ bác sĩ thành công!", "success")
        return jsonify(redirect=url_for("doctor_profile_detail"))

    return render_template("doctor_profile_edit.html", active_page="doctor-profile", profile=profile)

@app.route("/specializations")
@login_required
def select_specialization():
    profile_id = request.args.get("profile_id", type=int)
    profile = dao.get_patient_profile_by_id(profile_id)
    if not profile:
        flash("Hồ sơ khám không hợp lệ, vui lòng chọn lại", "error")
        return redirect(url_for("select_profile"))
    specializations = dao.get_all_specializations()
    spec_list = [
        {
            "id": s.id, "name": s.name, "icon": s.icon,
            "description": s.description or "Khám và tư vấn chuyên khoa.",
            "doctor_count": dao.count_available_doctors(s.id),
        }
        for s in specializations
    ]
    return render_template(
        "appointment_specialization.html",
        active_page="schedule",
        profile=profile,
        specializations=spec_list,
    )

@app.route("/doctors")
@login_required
def select_doctor():
    profile_id = request.args.get("profile_id", type=int)
    specialization_id = request.args.get("specialization_id", type=int)
    profile = dao.get_patient_profile_by_id(profile_id)
    specialization = dao.get_specialization_by_id(specialization_id)
    if not profile or not specialization:
        flash("Thông tin không hợp lệ, vui lòng chọn lại.", "error")
        return redirect(url_for("select_profile"))

    doctors = dao.get_doctors_by_specialization(specialization_id)
    doctor_list = [
        {
            "id": d.id,
            "name": d.user.name if d.user else "Bác sĩ",
            "experience": d.experienceYrs,
            "room": d.room,
            "bio": d.bio or d.description or "Bác sĩ giàu kinh nghiệm, tận tâm với bệnh nhân.",
            "fee": f"{int(d.fee):,}".replace(",", ".") + " ₫",
            "available_slots": len(dao.get_available_slots_for_doctor(d.id)),
        }
        for d in doctors
    ]
    return render_template(
        "appointment_doctors.html",
        active_page="schedule",
        profile=profile,
        specialization=specialization,
        doctors=doctor_list,
    )

_VN_WEEKDAYS = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
def _build_date_pills(slots):
    from bookingonline.models.models import WorkScheduleSessionEnum

    seen = {}
    today = datetime.now().date()
    for slot in slots:
        work_date = slot["work_date"]
        if work_date not in seen:
            if work_date == today:
                label_day = "Hôm nay"
            elif work_date == today + timedelta(days=1):
                label_day = "Ngày mai"
            else:
                label_day = _VN_WEEKDAYS[work_date.weekday()]
            seen[work_date] = {
                "iso": work_date.isoformat(),
                "label_day": label_day,
                "label_date": work_date.strftime("%d/%m"),
                "full_label": f"{label_day}, {work_date.strftime('%d/%m/%Y')}",
                "morning": [],
                "afternoon": [],
            }
        bucket = "morning" if slot["session"] == WorkScheduleSessionEnum.MORNING else "afternoon"
        seen[work_date][bucket].append(slot)

    return [seen[d] for d in sorted(seen.keys())]


@app.route("/schedules", methods=["GET", "POST"])
@login_required
def appointment_schedule():
    profile_id = request.values.get("profile_id", type=int)
    doctor_id = request.values.get("doctor_id", type=int)
    profile = dao.get_patient_profile_by_id(profile_id) if profile_id else None
    doctor = dao.get_doctor_by_id(doctor_id) if doctor_id else None
    if not profile or not doctor:
        if request.method == "GET" and not (profile_id or doctor_id):
            return redirect(url_for("select_profile"))
        flash("Thông tin không hợp lệ, vui lòng chọn lại", "error")
        return redirect(url_for("select_profile"))

    slots = dao.get_available_slots_for_doctor(doctor_id)

    if request.method == "POST":
        slot_value = request.form.get("slot_value", "")
        reason = request.form.get("reason", "").strip()
        override_conflict = request.form.get("override_conflict") == "1"
        work_schedule_id = None
        slot_time = None
        if slot_value and "|" in slot_value:
            wsid_str, time_str = slot_value.split("|", 1)
            try:
                work_schedule_id = int(wsid_str)
                slot_time = datetime.strptime(time_str, "%H:%M").time()
            except ValueError:
                work_schedule_id = None
        if not work_schedule_id or not slot_time:
            flash("Vui lòng chọn một khung giờ khám.", "warning")
            return redirect(url_for("appointment_schedule", profile_id=profile_id, doctor_id=doctor_id))
        work_schedule = dao.get_work_schedule_by_id(work_schedule_id)
        slot_in_range = (
            work_schedule
            and work_schedule.startTime <= slot_time < work_schedule.endTime
        )
        if (not work_schedule or not work_schedule.isAvailable
                or work_schedule.doctorId != doctor.id or not slot_in_range
                or dao.is_slot_taken(doctor.id, work_schedule.workDate, slot_time)):
            flash("Khung giờ bạn chọn không còn trống, vui lòng chọn khung giờ khác.", "error")
            return redirect(url_for(
                "appointment_schedule", profile_id=profile_id, doctor_id=doctor_id
            ))

        scheduled_date = work_schedule.workDate
        scheduled_time = slot_time
        conflict = dao.find_conflicting_appointment(profile.id, scheduled_date, scheduled_time)
        if conflict and not override_conflict:
            flash(f"Bạn đã có cuộc hẹn cùng giờ tại chuyên khoa {conflict.doctor.specialization.name}, bạn có chắc muốn đặt lịch không?", "warning")
            return render_template(
                "appointment_schedule.html",
                active_page="schedule",
                profile=profile, doctor=doctor,
                dates=_build_date_pills(slots),
                conflict=conflict,
                pending_slot_value=slot_value,
                pending_reason=reason,
            )

        config = dao.get_system_config()
        scheduled_dt = datetime.combine(scheduled_date, scheduled_time)
        if scheduled_dt - datetime.now() < timedelta(minutes=config.minimumBookingTime):
            flash("Đã quá giờ quy định đặt lịch, vui lòng đặt ngày khác", "warning")
            return redirect(url_for("appointment_schedule", profile_id=profile_id, doctor_id=doctor_id))

        appointment = dao.create_appointment(
            patient_profile=profile,
            doctor=doctor,
            work_schedule=work_schedule,
            scheduled_date=scheduled_date,
            scheduled_time=scheduled_time,
            reason=reason,
        )
        payment = dao.create_pending_payment(appointment, amount=doctor.fee)
        order_code, checkout_url, qr_code = utils.create_payos_payment_link(payment)
        dao.save_payment_gateway_info(payment, order_code, checkout_url, qr_code)
        return redirect(url_for("show_payment", payment_id=payment.id))

    return render_template(
        "appointment_schedule.html",
        active_page="schedule",
        profile=profile, doctor=doctor,
        dates=_build_date_pills(slots),
    )

@app.route("/payment/<int:payment_id>")
@login_required
def show_payment(payment_id):
    payment = dao.get_payment_by_id(payment_id)
    if not payment:
        flash("Không tìm thấy giao dịch thanh toán", "error")
        return redirect(url_for("select_profile"))
    expire_at = payment.createdAt + timedelta(minutes=15)
    return render_template(
        "appointment_payment.html",
        active_page="payment",
        payment=payment,
        expire_at=expire_at.isoformat(),
        qr_image_data_uri=utils.generate_qr_image_data_uri(payment.qrCode),
    )


@app.route("/payment/status/<int:payment_id>")
@login_required
def payment_status(payment_id):
    payment = dao.get_payment_by_id(payment_id)
    if not payment:
        if request.args.get("format") == "json":
            return jsonify({"status": "NOT_FOUND"})
        flash("Không tìm thấy giao dịch hoặc trạng thái chưa cập nhật.", "error")
        return redirect(url_for("select_profile"))

    if payment.status == PaymentStatusEnum.PENDING:
        if dao.is_payment_expired(payment):
            dao.cancel_pending_appointment(payment)
            flash("Thanh toán thất bại, vui lòng quay lại sau.", "error")
        else:
            gateway_status = utils.get_payos_payment_status(payment.transactionId)
            if gateway_status == "PAID":
                utils.finalize_paid_appointment(payment)  # Bước 14 + 15
                flash("Thanh toán thành công, lịch hẹn đã được xác nhận!", "success")
            elif gateway_status in ("CANCELLED", "EXPIRED", "FAILED"):
                dao.cancel_pending_appointment(payment)
                flash("Thanh toán thất bại, vui lòng quay lại sau.", "error")

    if request.args.get("format") == "json":
        return jsonify({
            "status": payment.status.value,
            "appointment_id": payment.appointment.id if payment.appointment else None,
        })

    if payment.status == PaymentStatusEnum.PAID:
        return redirect(url_for("appointment_success", appointment_id=payment.appointment.id))
    if payment.status == PaymentStatusEnum.FAILED:
        return redirect(url_for("select_profile"))
    return redirect(url_for("show_payment", payment_id=payment.id))

@app.route("/webhooks/payos", methods=["POST"])
def payos_webhook():
    webhook_data = utils.verify_payos_webhook(request.get_data())
    if not webhook_data:
        return jsonify({"error": "invalid signature"}), 400

    order_code = webhook_data.order_code
    payment = dao.get_payment_by_transaction_id(order_code)

    if payment and payment.status == PaymentStatusEnum.PENDING:
        if webhook_data.code == "00":
            utils.finalize_paid_appointment(payment)
        else:
            dao.cancel_pending_appointment(payment)

    return jsonify({"error": None})


@app.route("/appointment/success/<int:appointment_id>")
@login_required
def appointment_success(appointment_id):
    appointment = dao.get_appointment_by_id(appointment_id)
    if not appointment:
        flash("Không tìm thấy lịch hẹn.", "error")
        return redirect(url_for("select_profile"))
    return render_template(
        "appointment_success.html",
        active_page="success",
        appointment=appointment,
    )

@app.route("/my-appointments")
@login_required
def my_appointments():
    profiles = dao.get_patient_profiles_by_owner(current_user.id)
    profile_ids = [p.id for p in profiles]
    appointments = (
        Appointment.query
        .filter(Appointment.patientProfileId.in_(profile_ids))
        .order_by(Appointment.scheduledDate.desc(), Appointment.scheduledTime.desc())
        .all()
        if profile_ids else []
    )
    return render_template(
        "appointment_list.html",
        active_page="appointments",
        appointments=appointments,
    )

@app.route("/chatbot")
@login_required
def chatbot_stub():
    flash("Tính năng Chatbot gợi ý chuyên khoa sẽ được triển khai ở use case riêng.", "info")
    return redirect(url_for("select_profile"))

if __name__ == "__main__":
    app.run(debug=True)
