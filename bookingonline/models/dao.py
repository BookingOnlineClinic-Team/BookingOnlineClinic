import hashlib
from datetime import datetime, timedelta, date, time as dtime
from bookingonline import db
from bookingonline.models.models import *


def hash_password(password: str) -> str:
    return hashlib.md5(password.encode("utf-8")).hexdigest()

def get_user_by_username(username, role=None):
    q = User.query.filter_by(username=username)
    if role:
        q = q.filter_by(role=role)
    return q.first()

def verify_login(username, password, role=None):
    user = get_user_by_username(username, role)
    if user and user.password == password and user.active:
        return user
    return None

def create_patient_user(name, username, password, email, phone=None, gender=None):
    user = User(
        name=name, username=username, password=password,
        email=email, phone=phone, gender=gender,
        role=UserRoleEnum.PATIENT,
    )
    db.session.add(user)
    db.session.commit()
    return user

def get_system_config():
    config = SystemConfig.query.get(1)
    if not config:
        config = SystemConfig(
            id=1,
            minimumBookingTime=60,
            minimumCancellationTime=120,
            morningStartTime=dtime(7, 30),
            morningEndTime=dtime(11, 30),
            afternoonStartTime=dtime(13, 30),
            afternoonEndTime=dtime(17, 30),
            maxAppointmentsPerDay=1,
        )
        db.session.add(config)
        db.session.commit()
    return config

def get_all_specializations(active_only=True):
    # bichnhu - chỉ lây những chuyên khoa active - đang mở
    q = Specialization.query
    if active_only:
        q = q.filter(Specialization.active == True)
    # bichnhu
    return Specialization.query.order_by(Specialization.name).all()

def get_specialization_by_id(specialization_id):
    return Specialization.query.get(specialization_id)

def count_available_doctors(specialization_id):
    return (
        DoctorProfile.query
        .join(WorkSchedule, WorkSchedule.doctorId == DoctorProfile.id)
        .filter(
            DoctorProfile.specializationId == specialization_id,
            WorkSchedule.isAvailable == True,  # noqa: E712
            WorkSchedule.workDate >= date.today(),
        )
        .distinct()
        .count()
    )

def get_doctors_by_specialization(specialization_id):
    return DoctorProfile.query.filter_by(specializationId=specialization_id).all()

def get_doctor_by_id(doctor_id):
    return DoctorProfile.query.get(doctor_id)

def get_doctor_profile_by_user(user_id):
    return DoctorProfile.query.filter_by(userId=user_id).first()

def update_doctor_profile(profile, license_number, experience_yrs, fee, description=None, bio=None, avatar_url=None):
    profile.licenseNumber = license_number
    profile.experienceYrs = experience_yrs
    profile.fee = fee
    profile.description = description
    profile.bio = bio
    profile.avatarUrl = avatar_url
    db.session.commit()
    return profile

def get_available_work_schedules(doctor_id):
    today = date.today()
    monday_this_week = today - timedelta(days=today.weekday())
    end_date = monday_this_week + timedelta(days=13)
    return (
        WorkSchedule.query
        .filter(
            WorkSchedule.doctorId == doctor_id,
            WorkSchedule.isAvailable == True,
            WorkSchedule.workDate >= today,
            WorkSchedule.workDate <= end_date,
        )
        .order_by(WorkSchedule.workDate, WorkSchedule.startTime)
        .all()
    )


def split_time_range(start_time, end_time, slot_minutes=30):
    slots = []
    cur = datetime.combine(date.today(), start_time)
    end = datetime.combine(date.today(), end_time)
    while cur + timedelta(minutes=slot_minutes) <= end:
        slots.append((cur.time(), (cur + timedelta(minutes=slot_minutes)).time()))
        cur += timedelta(minutes=slot_minutes)
    return slots


def get_booked_times_for_doctor_date(doctor_id, work_date):
    rows = (
        Appointment.query
        .filter(
            Appointment.doctorId == doctor_id,
            Appointment.scheduledDate == work_date,
            Appointment.status == AppointmentStatusEnum.CONFIRMED,
        )
        .all()
    )
    return {r.scheduledTime for r in rows}


def get_available_slots_for_doctor(doctor_id, slot_minutes=30):
    blocks = get_available_work_schedules(doctor_id)
    slots = []
    booked_cache = {}
    for block in blocks:
        if block.workDate not in booked_cache:
            booked_cache[block.workDate] = get_booked_times_for_doctor_date(doctor_id, block.workDate)
        booked_times = booked_cache[block.workDate]

        for start_t, end_t in split_time_range(block.startTime, block.endTime, slot_minutes):
            if start_t in booked_times:
                continue
            slots.append({
                "work_schedule_id": block.id,
                "work_date": block.workDate,
                "session": block.session,
                "start": start_t,
                "end": end_t,
            })
    return slots


def is_slot_taken(doctor_id, work_date, work_time):
    return (
        Appointment.query
        .filter(
            Appointment.doctorId == doctor_id,
            Appointment.scheduledDate == work_date,
            Appointment.scheduledTime == work_time,
            Appointment.status == AppointmentStatusEnum.CONFIRMED,
        )
        .first() is not None
    )

def get_available_dates_for_doctor(doctor_id):
    schedules = get_available_work_schedules(doctor_id)
    seen = []
    for s in schedules:
        if s.workDate not in seen:
            seen.append(s.workDate)
    return seen

def get_work_schedules_for_doctor_on_date(doctor_id, work_date):
    return (
        WorkSchedule.query
        .filter(
            WorkSchedule.doctorId == doctor_id,
            WorkSchedule.workDate == work_date,
        )
        .order_by(WorkSchedule.startTime)
        .all()
    )

def get_work_schedule_by_id(work_schedule_id):
    return WorkSchedule.query.get(work_schedule_id)

def search_patient_profile(phone, name):
    return PatientHealthProfile.query.filter_by(phone=phone, name=name).first()


def get_patient_profiles_by_owner(user_id):
    return (
        PatientHealthProfile.query
        .filter_by(userId=user_id)
        .order_by(PatientHealthProfile.name)
        .all()
    )

def get_patient_profile_by_id(profile_id):
    return PatientHealthProfile.query.get(profile_id)

def create_patient_profile(owner, name, phone, gender=None, date_of_birth=None, address=None):
    profile = PatientHealthProfile(
        owner=owner,
        name=name,
        phone=phone,
        gender=gender,
        dateOfBirth=date_of_birth,
        address=address,
    )
    db.session.add(profile)
    db.session.commit()
    return profile

def get_patient_profile_by_owner(profile_id, user_id):
    return (
        PatientHealthProfile.query
        .filter(PatientHealthProfile.id == profile_id, PatientHealthProfile.userId == user_id)
        .first()
    )

def update_patient_profile(profile, name, phone, gender=None, date_of_birth=None, address=None):
    profile.name = name
    profile.phone = phone
    profile.gender = gender
    profile.dateOfBirth = date_of_birth
    profile.address = address
    db.session.commit()
    return profile

def find_conflicting_appointment(patient_profile_id, scheduled_date, scheduled_time):
    return (
        Appointment.query
        .filter(
            Appointment.patientProfileId == patient_profile_id,
            Appointment.scheduledDate == scheduled_date,
            Appointment.scheduledTime == scheduled_time,
            Appointment.status == AppointmentStatusEnum.CONFIRMED,
        )
        .first()
    )

def count_confirmed_appointments_on_date(patient_profile_id, scheduled_date):
    return (
        Appointment.query
        .filter(
            Appointment.patientProfileId == patient_profile_id,
            Appointment.scheduledDate == scheduled_date,
            Appointment.status == AppointmentStatusEnum.CONFIRMED,
        )
        .count()
    )

def create_appointment(patient_profile, doctor, work_schedule, scheduled_date,scheduled_time, reason, chatbot_suggestion=None):
    appointment = Appointment(
        patientProfile=patient_profile,
        doctor=doctor,
        workSchedule=work_schedule,
        scheduledDate=scheduled_date,
        scheduledTime=scheduled_time,
        status=AppointmentStatusEnum.CONFIRMED,
        reason=reason,
        chatbotSuggestion=chatbot_suggestion,
    )
    db.session.add(appointment)
    db.session.commit()
    return appointment


def create_pending_payment(appointment, amount):
    payment = Payment(
        appointment=appointment,
        amount=amount,
        status=PaymentStatusEnum.PENDING,
    )
    db.session.add(payment)
    db.session.commit()
    return payment


def save_payment_gateway_info(payment, transaction_id, checkout_url, qr_code):
    payment.transactionId = str(transaction_id)
    payment.checkoutUrl = checkout_url
    payment.qrCode = qr_code
    db.session.commit()
    return payment

def get_payment_by_id(payment_id):
    return Payment.query.get(payment_id)

def get_payment_by_transaction_id(transaction_id):
    return Payment.query.filter_by(transactionId=str(transaction_id)).first()

def confirm_payment_paid(payment):
    payment.status = PaymentStatusEnum.PAID
    payment.paidAt = datetime.now()
    db.session.commit()
    return payment

def mark_payment_failed(payment):
    payment.status = PaymentStatusEnum.FAILED
    db.session.commit()
    return payment

def is_payment_expired(payment, expire_minutes=15):
    if not payment or not payment.createdAt:
        return False
    return datetime.now() - payment.createdAt > timedelta(minutes=expire_minutes)

def cancel_pending_appointment(payment):
    appointment = payment.appointment
    db.session.delete(payment)
    if appointment:
        db.session.delete(appointment)
    db.session.commit()

def create_notification(user, title, body, ntype):
    notification = Notification(user=user, title=title, body=body, type=ntype)
    db.session.add(notification)
    db.session.commit()
    return notification

def get_unread_notification_count(user_id):
    return Notification.query.filter_by(userId=user_id, isRead=False).count()

def get_notifications_by_user(user_id, limit=10):
    return (
        Notification.query
        .filter_by(userId=user_id)
        .order_by(Notification.createdAt.desc())
        .limit(limit)
        .all()
    )

def get_appointment_by_id(appointment_id):
    return Appointment.query.get(appointment_id)

#--------------------ThaiHe---------------------
def get_doctors(keyword=None, specialization_id=None):
    query = (
        DoctorProfile.query
        .join(User, DoctorProfile.userId == User.id)
        .filter(
            User.role == UserRoleEnum.DOCTOR,
            User.active.is_(True)
        )
    )

    if keyword:
        keyword = keyword.strip()

        if keyword:
            query = query.filter(
                User.name.ilike(f"%{keyword}%")
            )

    if specialization_id:
        query = query.filter(
            DoctorProfile.specializationId == specialization_id
        )

    return query.order_by(User.name.asc()).all()

def get_doctor_detail(doctor_id):
    return (
        DoctorProfile.query
        .join(User, DoctorProfile.userId == User.id)
        .filter(
            DoctorProfile.id == doctor_id,
            User.role == UserRoleEnum.DOCTOR,
            User.active.is_(True)
        )
        .first()
    )

def get_reviews_by_doctor(doctor_id):
    return (
        Review.query
        .filter(Review.doctorId == doctor_id)
        .order_by(Review.time.desc())
        .all()
    )

def get_doctor_work_schedules_by_week(doctor_id, week_start):
    week_end = week_start + timedelta(days=6)

    return (
        WorkSchedule.query
        .filter(
            WorkSchedule.doctorId == doctor_id,
            WorkSchedule.workDate >= week_start,
            WorkSchedule.workDate <= week_end,
        )
        .order_by(
            WorkSchedule.workDate.asc(),
            WorkSchedule.startTime.asc()
        )
        .all()
    )

def get_week_start(target_date=None):
    target_date = target_date or date.today()

    return target_date - timedelta(
        days=target_date.weekday()
    )

def build_doctor_week_schedule(
        doctor_id,
        week_start
):
    schedules = get_doctor_work_schedules_by_week(
        doctor_id,
        week_start
    )

    appointments = get_doctor_appointments_by_week(
        doctor_id,
        week_start
    )

    schedule_map = {}

    for schedule in schedules:
        schedule_map[
            (
                schedule.workDate,
                schedule.session
            )
        ] = schedule

    appointment_map = {}

    for appointment in appointments:
        appointment_map.setdefault(
            appointment.scheduledDate,
            []
        ).append(appointment)

    days = []

    for offset in range(7):
        current_date = (
            week_start
            + timedelta(days=offset)
        )

        morning_appointments = []
        afternoon_appointments = []

        config = get_system_config()

        for appointment in appointment_map.get(
                current_date,
                []
        ):
            if appointment.scheduledTime < config.afternoonStartTime:
                morning_appointments.append(
                    appointment
                )
            else:
                afternoon_appointments.append(
                    appointment
                )

        days.append({
            "date": current_date,

            "morning": schedule_map.get(
                (
                    current_date,
                    WorkScheduleSessionEnum.MORNING
                )
            ),

            "afternoon": schedule_map.get(
                (
                    current_date,
                    WorkScheduleSessionEnum.AFTERNOON
                )
            ),

            "morning_appointments":
                morning_appointments,

            "afternoon_appointments":
                afternoon_appointments
        })

    return days

def get_work_schedule_by_doctor_date_session(
        doctor_id,
        work_date,
        session
):
    return (
        WorkSchedule.query
        .filter(
            WorkSchedule.doctorId == doctor_id,
            WorkSchedule.workDate == work_date,
            WorkSchedule.session == session
        )
        .first()
    )


def save_doctor_work_schedule(
        doctor_id,
        work_date,
        session,
        is_selected
):
    config = get_system_config()

    schedule = get_work_schedule_by_doctor_date_session(
        doctor_id,
        work_date,
        session
    )

    if session == WorkScheduleSessionEnum.MORNING:
        start_time = config.morningStartTime
        end_time = config.morningEndTime
    else:
        start_time = config.afternoonStartTime
        end_time = config.afternoonEndTime

    if is_selected:
        if schedule:
            schedule.startTime = start_time
            schedule.endTime = end_time
            schedule.isAvailable = True
        else:
            schedule = WorkSchedule(
                doctorId=doctor_id,
                workDate=work_date,
                session=session,
                startTime=start_time,
                endTime=end_time,
                isAvailable=True
            )
            db.session.add(schedule)

    elif schedule:

        if has_confirmed_appointment_in_schedule(schedule.id):
            raise ValueError(

                "Không thể bỏ ca làm việc đã có lịch hẹn được xác nhận."

            )

        schedule.isAvailable = False

    return schedule

def is_clinic_working_day(work_date):
    config = get_system_config()

    working_days = set(
        config.workingDaysList()
    )

    weekday_code = WEEKDAY_CODE.get(
        work_date.weekday()
    )

    return weekday_code in working_days

def update_doctor_week_schedule(
        doctor_id,
        week_start,
        selected_sessions
):
    for offset in range(7):
        work_date = week_start + timedelta(days=offset)

        if not is_clinic_working_day(work_date):
            continue

        morning_key = (
            f"{work_date.isoformat()}_MORNING"
        )

        afternoon_key = (
            f"{work_date.isoformat()}_AFTERNOON"
        )

        save_doctor_work_schedule(
            doctor_id=doctor_id,
            work_date=work_date,
            session=WorkScheduleSessionEnum.MORNING,
            is_selected=morning_key in selected_sessions
        )

        save_doctor_work_schedule(
            doctor_id=doctor_id,
            work_date=work_date,
            session=WorkScheduleSessionEnum.AFTERNOON,
            is_selected=afternoon_key in selected_sessions
        )

    db.session.commit()

def can_configure_schedule_week(week_start):
    today = date.today()

    current_week_start = get_week_start(today)

    next_week_start = (
        current_week_start
        + timedelta(days=7)
    )

    return week_start == next_week_start

def has_confirmed_appointment_in_schedule(schedule_id):
    return (
        Appointment.query
        .filter(
            Appointment.workScheduleId == schedule_id,
            Appointment.status == AppointmentStatusEnum.CONFIRMED
        )
        .first()
        is not None
    )

def get_doctor_appointments_by_week(
        doctor_id,
        week_start
):
    week_end = week_start + timedelta(days=6)

    return (
        Appointment.query
        .filter(
            Appointment.doctorId == doctor_id,
            Appointment.scheduledDate >= week_start,
            Appointment.scheduledDate <= week_end,
            Appointment.status != AppointmentStatusEnum.CANCELLED
        )
        .order_by(
            Appointment.scheduledDate.asc(),
            Appointment.scheduledTime.asc()
        )
        .all()
    )

# Chatbot - bichnhu
WEEKDAY_CODE = {
    0: "MONDAY", 1: "TUESDAY", 2: "WEDNESDAY", 3: "THURSDAY",
    4: "FRIDAY", 5: "SATURDAY", 6: "SUNDAY",
}

def get_allowed_booking_dates(days_ahead=14):
    #các ngày được phép đặt lịch, dựa trên ngày làm việc
    #của phòng khám (SystemConfig.workingDays) và thời gian đặt tối thiểu.
    config = get_system_config()
    working_days = set(config.workingDaysList())
    today = date.today()
    now = datetime.now()
    result = []
    for i in range(days_ahead):
        d = today + timedelta(days=i)
        if WEEKDAY_CODE[d.weekday()] not in working_days:
            continue
        if d == today:
            end_of_day = datetime.combine(d, config.afternoonEndTime)
            if now + timedelta(minutes=config.minimumBookingTime) >= end_of_day:
                continue
        result.append(d)
    return result


def get_specializations_brief():
    #Danh sách chuyên khoa (id, tên, mô tả) để đưa vào ngữ cảnh cho AI phân loại.
    return [
        {"id": s.id, "name": s.name, "description": s.description or ""}
        for s in get_all_specializations()
    ]


def get_available_slots_for_doctor_on_date(doctor_id, work_date, slot_minutes=30):
    #lọc theo 1 ngày cụ thể
    #(dùng cho chatbot vì bệnh nhân đã chọn ngày trước khi mô tả triệu chứng).
    blocks = get_work_schedules_for_doctor_on_date(doctor_id, work_date)
    booked_times = get_booked_times_for_doctor_date(doctor_id, work_date)
    slots = []
    for block in blocks:
        if not block.isAvailable:
            continue
        for start_t, end_t in split_time_range(block.startTime, block.endTime, slot_minutes):
            if start_t in booked_times:
                continue
            slots.append({
                "work_schedule_id": block.id,
                "work_date": block.workDate,
                "session": block.session,
                "start": start_t,
                "end": end_t,
            })
    return slots


def get_doctors_with_slots_by_specialization_on_date(
    specialization_id, work_date, slot_minutes=30, doctor_limit=5, slot_limit=8
):
    #tra cứu bác sĩ thuộc chuyên khoa + khung giờ trống trong ngày đã chọn.
    doctors = get_doctors_by_specialization(specialization_id)
    result = []
    for d in doctors:
        slots = get_available_slots_for_doctor_on_date(d.id, work_date, slot_minutes)
        if not slots:
            continue
        result.append({"doctor": d, "slots": slots[:slot_limit]})
    result.sort(key=lambda x: (x["doctor"].averageRating or 0), reverse=True)
    return result[:doctor_limit]


def create_chatbot_session(user, query_text, booked_date, specialization_id=None, ai_requirements=None):
    session = ChatbotSession(
        userId=user.id,
        queryText=query_text,
        bookedDate=booked_date,
        specializationId=specialization_id,
        aiRequirements=ai_requirements,
    )
    db.session.add(session)
    db.session.commit()
    return session


def update_chatbot_session_specialization(session, specialization_id, ai_requirements=None):
    session.specializationId = specialization_id
    if ai_requirements is not None:
        session.aiRequirements = ai_requirements
    db.session.commit()
    return session


def add_chatbot_doctor_suggestion(session_id, doctor_id, available_date, start_time, end_time, reason=None):
    suggestion = ChatbotDoctorSuggestion(
        sessionId=session_id,
        doctorId=doctor_id,
        availableDate=available_date,
        startTime=start_time,
        endTime=end_time,
        reason=reason,
    )
    db.session.add(suggestion)
    db.session.commit()
    return suggestion


def get_chatbot_session_by_id(session_id):
    return ChatbotSession.query.get(session_id)


def get_chatbot_suggestion_by_id(suggestion_id):
    return ChatbotDoctorSuggestion.query.get(suggestion_id)

#BichNhu - Admin - cấu hình tham số
def update_system_config(config, **data):
    #Cập nhật các field của SystemConfig (singleton, id=1). Bỏ qua field
    #có giá trị None (nghĩa là không đổi giá trị đó).
    for key, value in data.items():
        if value is not None:
            setattr(config, key, value)
    db.session.commit()
    return config


def count_active_appointments_on_date(patient_profile_id, work_date):
    #Đếm số lịch hẹn còn hiệu lực (không tính CANCELLED) của 1 bệnh nhân
    #trong 1 ngày - dùng để áp dụng SystemConfig.maxAppointmentsPerDay.
    return (
        Appointment.query
        .filter(
            Appointment.patientProfileId == patient_profile_id,
            Appointment.scheduledDate == work_date,
            Appointment.status != AppointmentStatusEnum.CANCELLED,
        )
        .count()
    )

# bichnhu - admin - quan ly chuyên khoa
def is_specialization_name_taken(name, exclude_id=None):
    q = Specialization.query.filter(db.func.lower(Specialization.name) == name.strip().lower())
    if exclude_id:
        q = q.filter(Specialization.id != exclude_id)
    return db.session.query(q.exists()).scalar()

def create_specialization(name, icon=None, description=None):
    spec = Specialization(
        name=name.strip(),
        icon=(icon or "stethoscope").strip(),
        description=(description or "").strip() or None,
        active=True,
    )
    db.session.add(spec)
    db.session.commit()
    return spec

def update_specialization(specialization, name, icon=None, description=None):
    specialization.name = name.strip()
    specialization.icon = (icon or "stethoscope").strip()
    specialization.description = (description or "").strip() or None
    db.session.commit()
    return specialization

def toggle_specialization_active(specialization):
    #Khóa / Mở khóa chuyên khoa. Không xóa dữ liệu, chỉ ẩn/hiện khỏi luồng đặt lịch.
    specialization.active = not specialization.active
    db.session.commit()
    return specialization

def count_doctors_in_specialization(specialization_id):
    return DoctorProfile.query.filter_by(specializationId=specialization_id).count()

def delete_specialization(specialization):
    #Xóa cứng. Chặn nếu còn bác sĩ trực thuộc để tránh lỗi khóa ngoại / mất dữ liệu.
    if count_doctors_in_specialization(specialization.id) > 0:
        return False, "Không thể xóa: chuyên khoa đang có bác sĩ trực thuộc. Hãy chuyển bác sĩ sang chuyên khoa khác, hoặc dùng chức năng Khóa thay vì Xóa."
    db.session.delete(specialization)
    db.session.commit()
    return True, None

# bichnhu - admin - quản lý tài khoản bác sĩ (User + DoctorProfile)

def is_username_taken(username, exclude_user_id=None):
    # Kiểm tra username đã tồn tại chưa (không phân biệt hoa/thường)
    q = User.query.filter(db.func.lower(User.username) == username.strip().lower())
    if exclude_user_id:
        q = q.filter(User.id != exclude_user_id)
    return db.session.query(q.exists()).scalar()


def get_all_doctors_admin(keyword=None, specialization_id=None):
    # Danh sách TẤT CẢ bác sĩ dùng cho trang quản lý của admin.
    # Khác với get_doctors(): KHÔNG lọc User.active, vì admin cần thấy
    # cả những bác sĩ đang bị khóa để có thể mở khóa lại.
    query = (
        DoctorProfile.query
        .join(User, DoctorProfile.userId == User.id)
        .filter(User.role == UserRoleEnum.DOCTOR)
    )
    if keyword:
        keyword = keyword.strip()
        if keyword:
            query = query.filter(
                db.or_(
                    User.name.ilike(f"%{keyword}%"),
                    User.username.ilike(f"%{keyword}%"),
                )
            )
    if specialization_id:
        query = query.filter(DoctorProfile.specializationId == specialization_id)
    return query.order_by(User.name.asc()).all()


def create_doctor_account(
    name, username, password, email, specialization_id,
    license_number, experience_yrs, fee,
    phone=None, gender=None, description=None, bio=None, avatar_url=None,
):
    # Tạo TÀI KHOẢN bác sĩ hoàn chỉnh: 1 User (role=DOCTOR) + 1 DoctorProfile
    # đi kèm, trong cùng một transaction. Nếu lỗi giữa chừng -> rollback,
    # tránh tạo ra User "mồ côi" (không có DoctorProfile đi kèm).
    try:
        user = User(
            name=name,
            username=username,
            # Lưu plaintext để đồng bộ với verify_login() hiện tại của project
            # (chưa hash password ở bất kỳ đâu). Muốn bảo mật hơn thì đổi thành
            # password=dao.hash_password(password) VÀ sửa luôn verify_login().
            password=password,
            email=email,
            phone=phone,
            gender=gender,
            role=UserRoleEnum.DOCTOR,
            active=True,
        )
        db.session.add(user)
        db.session.flush()  # flush để có user.id ngay, chưa commit vội

        profile = DoctorProfile(
            userId=user.id,
            specializationId=specialization_id,
            licenseNumber=license_number,
            experienceYrs=experience_yrs,
            fee=fee,
            description=description,
            bio=bio,
            avatarUrl=avatar_url,
        )
        db.session.add(profile)
        db.session.commit()
        return user, profile
    except Exception:
        db.session.rollback()
        raise


def update_doctor_account(doctor, name, email, specialization_id,
                           license_number, experience_yrs, fee,
                           phone=None, gender=None, description=None, bio=None, avatar_url=None):
    # Sửa thông tin User + DoctorProfile của 1 bác sĩ đã tồn tại.
    # KHÔNG đổi username/password ở đây (dùng route reset-password riêng cho mật khẩu).
    user = doctor.user
    user.name = name
    user.email = email
    user.phone = phone
    user.gender = gender

    doctor.specializationId = specialization_id
    doctor.licenseNumber = license_number
    doctor.experienceYrs = experience_yrs
    doctor.fee = fee
    doctor.description = description
    doctor.bio = bio
    doctor.avatarUrl = avatar_url
    db.session.commit()
    return doctor


def toggle_doctor_active(doctor):
    # Khóa / Mở khóa tài khoản đăng nhập của bác sĩ (không xóa dữ liệu).
    # User.active=False -> bác sĩ không login được, đồng thời tự động bị ẩn
    # khỏi danh sách đặt lịch công khai (get_doctors()/get_doctor_detail() đã lọc User.active).
    user = doctor.user
    user.active = not user.active
    db.session.commit()
    return doctor


def reset_doctor_password(doctor, new_password):
    # Admin đặt lại mật khẩu mới cho bác sĩ (dùng khi bác sĩ quên mật khẩu)
    doctor.user.password = new_password
    db.session.commit()
    return doctor

# bichnhu - admin - quản lý bệnh nhân (chỉ xem danh sách + khóa/mở khóa)

def get_user_by_id(user_id):
    # Hàm tiện ích chung, dùng cho các thao tác trên User (không riêng bệnh nhân)
    return User.query.get(user_id)


def get_all_patients_admin(keyword=None):
    # Danh sách TẤT CẢ tài khoản bệnh nhân cho trang quản lý của admin.
    # Không lọc active, vì admin cần thấy cả tài khoản đã bị khóa để mở lại.
    query = User.query.filter(User.role == UserRoleEnum.PATIENT)
    if keyword:
        keyword = keyword.strip()
        if keyword:
            like = f"%{keyword}%"
            query = query.filter(
                db.or_(
                    User.name.ilike(like),
                    User.username.ilike(like),
                    User.email.ilike(like),
                    User.phone.ilike(like),
                )
            )
    return query.order_by(User.name.asc()).all()


def count_health_profiles_for_patient(user_id):
    # Số hồ sơ sức khỏe (có thể là của người thân) mà tài khoản này đang quản lý
    return PatientHealthProfile.query.filter_by(userId=user_id).count()


def count_appointments_for_patient(user_id):
    # Tổng số lịch hẹn đã đặt qua tất cả hồ sơ sức khỏe thuộc tài khoản này
    return (
        Appointment.query
        .join(PatientHealthProfile, Appointment.patientProfileId == PatientHealthProfile.id)
        .filter(PatientHealthProfile.userId == user_id)
        .count()
    )


def toggle_user_active(user):
    # Khóa / Mở khóa tài khoản (dùng chung được cho patient, doctor...).
    # active=False -> không login được nữa (verify_login đã kiểm tra user.active).
    user.active = not user.active
    db.session.commit()
    return user