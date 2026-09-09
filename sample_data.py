from datetime import date, time, datetime, timedelta
from bookingonline.models import dao
from bookingonline import db, app
from bookingonline.models.models import *

def find_slot(work_schedules, doctor, work_date, session):
    return next(
        (ws for ws in work_schedules
         if ws.doctor is doctor
         and ws.workDate == work_date
         and ws.session == session),
        None,
    )


def seed():
    db.drop_all()
    db.create_all()

    # ---------------------------------------------------
    # 1. SystemConfig (singleton)
    # ---------------------------------------------------
    config = SystemConfig(
        id=1,
        minimumBookingTime=60,
        minimumCancellationTime=120,
        workingDays="MONDAY,TUESDAY,WEDNESDAY,THURSDAY,FRIDAY,SATURDAY",
        morningStartTime=time(7, 30),
        morningEndTime=time(11, 30),
        afternoonStartTime=time(13, 0),
        afternoonEndTime=time(17, 0),
        maxAppointmentsPerDay=1,
        refundPercentagePatient=100,
        refundPercentageDoctor=100,
    )
    db.session.add(config)

    # ---------------------------------------------------
    # 2. Specialization
    # ---------------------------------------------------
    spec_noi = Specialization(name="Nội tổng quát", icon="stethoscope",
                               description="Khám và điều trị các bệnh lý nội khoa tổng quát.")
    spec_nhi = Specialization(name="Nhi khoa", icon="baby",
                               description="Khám, tư vấn dinh dưỡng và điều trị bệnh cho trẻ em.")
    spec_da_lieu = Specialization(name="Da liễu", icon="hand-sparkles",
                                   description="Khám và điều trị các bệnh lý về da, tóc, móng.")
    spec_tim_mach = Specialization(name="Tim mạch", icon="heart-pulse",
                                    description="Khám, tầm soát và điều trị các bệnh lý tim mạch.")
    db.session.add_all([spec_noi, spec_nhi, spec_da_lieu, spec_tim_mach])
    db.session.flush()  # để có id trước khi tham chiếu bên dưới

    # ---------------------------------------------------
    # 3. Users: admin, doctors, patients
    # ---------------------------------------------------
    admin = User(
        name="Quản trị viên",
        username="admin",
        email="admin@clinic.vn",
        password="Admin@123",
        role=UserRoleEnum.ADMIN,
        gender=GenderEnum.MALE,
        phone="0900000000",
    )

    doctor_user_1 = User(
        name="BS. Nguyễn Thị Hoa",
        username="d1",
        email="phuquy141105@gmail.com",
        password="Doctor@123",
        role=UserRoleEnum.DOCTOR,
        gender=GenderEnum.FEMALE,
        phone="0901111111",
    )
    doctor_user_2 = User(
        name="BS. Trần Văn Nam",
        username="d2",
        email="phuquy141105@gmail.com",
        password="Doctor@123",
        role=UserRoleEnum.DOCTOR,
        gender=GenderEnum.MALE,
        phone="0902222222",
    )
    doctor_user_3 = User(
        name="BS. Phạm Thuỳ Linh",
        username="d3",
        email="phuquy141105@gmail.com",
        password="Doctor@123",
        role=UserRoleEnum.DOCTOR,
        gender=GenderEnum.FEMALE,
        phone="0903333333",
    )
    doctor_user_4 = User(
        name="BS. Lê Quốc Huy",
        username="d4",
        email="phuquy141105@gmail.com",
        password="Doctor@123",
        role=UserRoleEnum.DOCTOR,
        gender=GenderEnum.MALE,
        phone="0904444444",
    )

    patient_user_1 = User(
        name="Nguyễn Văn Bình",
        username="p1",
        email="phuquy141105@gmail.com",
        password="Patient@123",
        role=UserRoleEnum.PATIENT,
        gender=GenderEnum.MALE,
        phone="0911111111",
    )
    patient_user_2 = User(
        name="Trần Thị Mai",
        username="p2",
        email="phuquy141105@gmail.com",
        password="Patient@123",
        role=UserRoleEnum.PATIENT,
        gender=GenderEnum.FEMALE,
        phone="0912222222",
    )
    patient_user_3 = User(
        name="Lê Văn Cường",
        username="p3",
        email="phuquy141105@gmail.com",
        password="Patient@123",
        role=UserRoleEnum.PATIENT,
        gender=GenderEnum.MALE,
        phone="0913333333",
    )
    patient_user_4 = User(
        name="Phạm Thị Hạnh",
        username="p4",
        email="phuquy141105@gmail.com",
        password="Patient@123",
        role=UserRoleEnum.PATIENT,
        gender=GenderEnum.FEMALE,
        phone="0914444444",
    )

    db.session.add_all([
        admin,
        doctor_user_1, doctor_user_2, doctor_user_3, doctor_user_4,
        patient_user_1, patient_user_2, patient_user_3, patient_user_4,
    ])
    db.session.flush()

    # ---------------------------------------------------
    # 4. DoctorProfile (gán qua object "user"/"specialization")
    # ---------------------------------------------------
    doctor_1 = DoctorProfile(
        user=doctor_user_1,
        specialization=spec_noi,
        licenseNumber="BS-001-2015",
        experienceYrs=10,
        description="Chuyên khám và điều trị các bệnh lý nội tổng quát.",
        bio="Tốt nghiệp Đại học Y Dược TP.HCM, 10 năm kinh nghiệm.",
        room="Phòng 101, Lầu 1",
        totalReview=2,
        averageRating=4.5,
        avatarUrl="https://example.com/avatars/bs_hoa.jpg",
        fee=250000,
    )
    doctor_2 = DoctorProfile(
        user=doctor_user_2,
        specialization=spec_tim_mach,
        licenseNumber="BS-002-2012",
        experienceYrs=13,
        description="Chuyên khoa Tim mạch, siêu âm tim, điện tâm đồ.",
        bio="13 năm kinh nghiệm tại các bệnh viện tuyến trung ương.",
        room="Phòng 202, Lầu 2",
        totalReview=1,
        averageRating=5.0,
        avatarUrl="https://example.com/avatars/bs_nam.jpg",
        fee=300000,
    )
    doctor_3 = DoctorProfile(
        user=doctor_user_3,
        specialization=spec_nhi,
        licenseNumber="BS-003-2018",
        experienceYrs=7,
        description="Chuyên khám nhi, tư vấn dinh dưỡng trẻ em.",
        bio="7 năm kinh nghiệm khám nhi khoa.",
        room="Phòng 105, Lầu 1",
        totalReview=0,
        averageRating=0.0,
        avatarUrl="https://example.com/avatars/bs_linh.jpg",
        fee=200000,
    )
    doctor_4 = DoctorProfile(
        user=doctor_user_4,
        specialization=spec_da_lieu,
        licenseNumber="BS-004-2020",
        experienceYrs=5,
        description="Chuyên khám và điều trị các bệnh lý về da liễu, thẩm mỹ da.",
        bio="5 năm kinh nghiệm khám da liễu tại các phòng khám tư nhân.",
        room="Phòng 301, Lầu 3",
        totalReview=0,
        averageRating=0.0,
        avatarUrl="https://example.com/avatars/bs_huy.jpg",
        fee=220000,
    )

    db.session.add_all([doctor_1, doctor_2, doctor_3, doctor_4])
    db.session.flush()

    # ---------------------------------------------------
    # 5. PatientHealthProfile
    #    -> MỌI bệnh nhân (role PATIENT) đều có ít nhất 1 hồ sơ sức khỏe.
    #    - Bình: 1 hồ sơ cho chính mình
    #    - Mai: 2 hồ sơ (chính mình + con)
    #    - Cường: 1 hồ sơ cho chính mình
    #    - Hạnh: 2 hồ sơ (chính mình + con)
    # ---------------------------------------------------
    profile_binh = PatientHealthProfile(
        owner=patient_user_1,
        name="Nguyễn Văn Bình",
        phone="0911111111",
        gender=GenderEnum.MALE,
        dateOfBirth=date(1990, 5, 20),
        address="12 Nguyễn Trãi, Quận 1, TP.HCM",
    )
    profile_mai = PatientHealthProfile(
        owner=patient_user_2,
        name="Trần Thị Mai",
        phone="0912222222",
        gender=GenderEnum.FEMALE,
        dateOfBirth=date(1988, 3, 15),
        address="45 Lê Lợi, Quận 3, TP.HCM",
    )
    profile_con_mai = PatientHealthProfile(
        owner=patient_user_2,  # đặt lịch hộ: vẫn thuộc tài khoản của Mai
        name="Trần Gia Bảo",
        phone="0912222222",
        gender=GenderEnum.MALE,
        dateOfBirth=date(2019, 7, 1),
        address="45 Lê Lợi, Quận 3, TP.HCM",
    )
    profile_cuong = PatientHealthProfile(
        owner=patient_user_3,
        name="Lê Văn Cường",
        phone="0913333333",
        gender=GenderEnum.MALE,
        dateOfBirth=date(1995, 11, 2),
        address="78 Cách Mạng Tháng 8, Quận 10, TP.HCM",
    )
    profile_hanh = PatientHealthProfile(
        owner=patient_user_4,
        name="Phạm Thị Hạnh",
        phone="0914444444",
        gender=GenderEnum.FEMALE,
        dateOfBirth=date(1992, 9, 9),
        address="23 Điện Biên Phủ, Bình Thạnh, TP.HCM",
    )
    profile_con_hanh = PatientHealthProfile(
        owner=patient_user_4,  # đặt lịch hộ cho con
        name="Phạm Gia Khang",
        phone="0914444444",
        gender=GenderEnum.MALE,
        dateOfBirth=date(2020, 2, 14),
        address="23 Điện Biên Phủ, Bình Thạnh, TP.HCM",
    )
    db.session.add_all([
        profile_binh, profile_mai, profile_con_mai,
        profile_cuong, profile_hanh, profile_con_hanh,
    ])
    db.session.flush()

    # ---------------------------------------------------
    # 6. WorkSchedule cho tuần hiện tại (Mon-Sat, 4 bác sĩ)
    # ---------------------------------------------------
    today = date.today()
    monday_this_week = today - timedelta(days=today.weekday())

    all_doctors = (doctor_1, doctor_2, doctor_3, doctor_4)
    work_schedules = []
    for day_offset in range(6):  # Mon-Sat theo workingDays ở SystemConfig
        work_date = monday_this_week + timedelta(days=day_offset)
        for doctor in all_doctors:
            work_schedules.append(WorkSchedule(
                doctor=doctor,
                workDate=work_date,
                session=WorkScheduleSessionEnum.MORNING,
                startTime=time(7, 30),
                endTime=time(11, 30),
                isAvailable=True,
            ))
            work_schedules.append(WorkSchedule(
                doctor=doctor,
                workDate=work_date,
                session=WorkScheduleSessionEnum.AFTERNOON,
                startTime=time(13, 0),
                endTime=time(17, 0),
                isAvailable=True,
            ))
    db.session.add_all(work_schedules)
    db.session.flush()

    slot_doctor1_mon_morning = find_slot(work_schedules, doctor_1, monday_this_week, WorkScheduleSessionEnum.MORNING)
    slot_doctor3_mon_afternoon = find_slot(work_schedules, doctor_3, monday_this_week, WorkScheduleSessionEnum.AFTERNOON)
    tuesday_this_week = monday_this_week + timedelta(days=1)
    slot_doctor4_tue_morning = find_slot(work_schedules, doctor_4, tuesday_this_week, WorkScheduleSessionEnum.MORNING)

    # ---------------------------------------------------
    # 7. ChatbotSession + ChatbotDoctorSuggestion (UC_03)
    # ---------------------------------------------------
    chatbot_session_1 = ChatbotSession(
        user=patient_user_1,
        specialization=spec_noi,
        bookedDate=monday_this_week,
        queryText="Tôi bị đau bụng âm ỉ vùng thượng vị, kèm buồn nôn 2 ngày nay.",
        aiRequirements="Phân tích triệu chứng liên quan tiêu hóa / nội tổng quát.",
    )
    chatbot_session_2 = ChatbotSession(
        user=patient_user_3,
        specialization=spec_da_lieu,
        bookedDate=tuesday_this_week,
        queryText="Da mặt tôi nổi mẩn đỏ, ngứa rát 3 ngày nay, nghi dị ứng mỹ phẩm.",
        aiRequirements="Phân tích triệu chứng liên quan da liễu / dị ứng.",
    )
    db.session.add_all([chatbot_session_1, chatbot_session_2])
    db.session.flush()

    suggestion_1 = ChatbotDoctorSuggestion(
        session=chatbot_session_1,
        doctor=doctor_1,
        availableDate=monday_this_week,
        startTime=time(8, 0),
        endTime=time(8, 30),
        reason="Triệu chứng phù hợp chuyên khoa Nội tổng quát.",
    )
    suggestion_2 = ChatbotDoctorSuggestion(
        session=chatbot_session_2,
        doctor=doctor_4,
        availableDate=tuesday_this_week,
        startTime=time(8, 0),
        endTime=time(8, 30),
        reason="Triệu chứng phù hợp chuyên khoa Da liễu.",
    )
    db.session.add_all([suggestion_1, suggestion_2])
    db.session.flush()

    # ---------------------------------------------------
    # 8. Appointment (UC_01) + Payment
    # ---------------------------------------------------
    appointments = []
    payments = []

    # 8.1 Sinh từ gợi ý chatbot - Bình khám Nội với BS. Hoa (CONFIRMED, đã thanh toán)
    appointment_1 = Appointment(
        patientProfile=profile_binh,
        doctor=doctor_1,
        workSchedule=slot_doctor1_mon_morning,
        chatbotSuggestion=suggestion_1,
        scheduledDate=monday_this_week,
        scheduledTime=time(8, 0),
        status=AppointmentStatusEnum.CONFIRMED,
        reason="Đau bụng âm ỉ vùng thượng vị, buồn nôn.",
    )
    payment_1 = Payment(
        appointment=appointment_1,
        amount=doctor_1.fee,
        status=PaymentStatusEnum.PAID,
        transactionId="TXN-0001",
        checkoutUrl="https://payos.vn/checkout/TXN-0001",
        qrCode="QR-CODE-TXN-0001",
        paidAt=datetime.now(),
    )
    appointments.append(appointment_1)
    payments.append(payment_1)

    # 8.2 Mai đặt hộ cho con (Bảo) khám Nhi với BS. Linh (CONFIRMED, đã thanh toán)
    appointment_2 = Appointment(
        patientProfile=profile_con_mai,
        doctor=doctor_3,
        workSchedule=slot_doctor3_mon_afternoon,
        scheduledDate=monday_this_week,
        scheduledTime=time(13, 30),
        status=AppointmentStatusEnum.CONFIRMED,
        reason="Khám định kỳ, tư vấn dinh dưỡng.",
    )
    payment_2 = Payment(
        appointment=appointment_2,
        amount=doctor_3.fee,
        status=PaymentStatusEnum.PAID,
        transactionId="TXN-0002",
        checkoutUrl="https://payos.vn/checkout/TXN-0002",
        qrCode="QR-CODE-TXN-0002",
        paidAt=datetime.now(),
    )
    appointments.append(appointment_2)
    payments.append(payment_2)

    # 8.3 Mai khám Tim mạch với BS. Nam - đã hoàn thành tuần trước (đủ điều kiện đánh giá UC_06)
    last_monday = monday_this_week - timedelta(days=7)
    appointment_3 = Appointment(
        patientProfile=profile_mai,
        doctor=doctor_2,
        scheduledDate=last_monday,
        scheduledTime=time(9, 0),
        status=AppointmentStatusEnum.COMPLETED,
        reason="Khám tim mạch định kỳ.",
    )
    payment_3 = Payment(
        appointment=appointment_3,
        amount=doctor_2.fee,
        status=PaymentStatusEnum.PAID,
        transactionId="TXN-0003",
        checkoutUrl="https://payos.vn/checkout/TXN-0003",
        qrCode="QR-CODE-TXN-0003",
        paidAt=datetime.combine(last_monday, time(9, 0)),
    )
    appointments.append(appointment_3)
    payments.append(payment_3)

    # 8.4 Bình hủy lịch khám Tim mạch với BS. Nam (CANCELLED bởi bệnh nhân, hoàn phí 100%)
    appointment_4 = Appointment(
        patientProfile=profile_binh,
        doctor=doctor_2,
        scheduledDate=monday_this_week + timedelta(days=2),
        scheduledTime=time(10, 0),
        status=AppointmentStatusEnum.CANCELLED,
        reason="Khám tim mạch.",
        cancelledByUser=patient_user_1,
        cancelReason="Bận việc đột xuất, không thể đến khám.",
        cancelledAt=datetime.now(),
    )
    payment_4 = Payment(
        appointment=appointment_4,
        amount=doctor_2.fee,
        status=PaymentStatusEnum.REFUND,
        transactionId="TXN-0004",
        checkoutUrl="https://payos.vn/checkout/TXN-0004",
        qrCode="QR-CODE-TXN-0004",
        paidAt=datetime.now() - timedelta(days=1),
    )
    appointments.append(appointment_4)
    payments.append(payment_4)

    # 8.5 Sinh từ gợi ý chatbot - Cường khám Da liễu với BS. Huy (CONFIRMED, chưa thanh toán)
    appointment_5 = Appointment(
        patientProfile=profile_cuong,
        doctor=doctor_4,
        workSchedule=slot_doctor4_tue_morning,
        chatbotSuggestion=suggestion_2,
        scheduledDate=tuesday_this_week,
        scheduledTime=time(8, 0),
        status=AppointmentStatusEnum.CONFIRMED,
        reason="Da mặt nổi mẩn đỏ, ngứa rát, nghi dị ứng mỹ phẩm.",
    )
    payment_5 = Payment(
        appointment=appointment_5,
        amount=doctor_4.fee,
        status=PaymentStatusEnum.PENDING,
        transactionId="TXN-0005",
        checkoutUrl="https://payos.vn/checkout/TXN-0005",
        qrCode="QR-CODE-TXN-0005",
        paidAt=None,
    )
    appointments.append(appointment_5)
    payments.append(payment_5)

    # 8.6 Hạnh khám Nội với BS. Hoa nhưng KHÔNG đến khám (NO_SHOW), đã thanh toán trước, không hoàn phí
    last_friday = monday_this_week - timedelta(days=3)
    appointment_6 = Appointment(
        patientProfile=profile_hanh,
        doctor=doctor_1,
        scheduledDate=last_friday,
        scheduledTime=time(9, 30),
        status=AppointmentStatusEnum.NO_SHOW,
        reason="Đau đầu, mệt mỏi kéo dài.",
    )
    payment_6 = Payment(
        appointment=appointment_6,
        amount=doctor_1.fee,
        status=PaymentStatusEnum.PAID,
        transactionId="TXN-0006",
        checkoutUrl="https://payos.vn/checkout/TXN-0006",
        qrCode="QR-CODE-TXN-0006",
        paidAt=datetime.combine(last_friday, time(9, 30)) - timedelta(hours=2),
    )
    appointments.append(appointment_6)
    payments.append(payment_6)

    # 8.7 Con của Hạnh (Khang) khám Nhi với BS. Linh - đã hoàn thành, chưa đánh giá
    two_weeks_ago_wed = monday_this_week - timedelta(days=12)
    appointment_7 = Appointment(
        patientProfile=profile_con_hanh,
        doctor=doctor_3,
        scheduledDate=two_weeks_ago_wed,
        scheduledTime=time(14, 0),
        status=AppointmentStatusEnum.COMPLETED,
        reason="Khám định kỳ, theo dõi tăng trưởng.",
    )
    payment_7 = Payment(
        appointment=appointment_7,
        amount=doctor_3.fee,
        status=PaymentStatusEnum.PAID,
        transactionId="TXN-0007",
        checkoutUrl="https://payos.vn/checkout/TXN-0007",
        qrCode="QR-CODE-TXN-0007",
        paidAt=datetime.combine(two_weeks_ago_wed, time(14, 0)),
    )
    appointments.append(appointment_7)
    payments.append(payment_7)

    # 8.8 & 8.9: Bình và Cường từng khám Nội với BS. Hoa - đã hoàn thành + đã đánh giá
    # (để dữ liệu review khớp với totalReview=2, averageRating=4.5 của doctor_1)
    two_weeks_ago_tue = monday_this_week - timedelta(days=13)
    appointment_8 = Appointment(
        patientProfile=profile_binh,
        doctor=doctor_1,
        scheduledDate=two_weeks_ago_tue,
        scheduledTime=time(8, 30),
        status=AppointmentStatusEnum.COMPLETED,
        reason="Đau bụng tái khám.",
    )
    payment_8 = Payment(
        appointment=appointment_8,
        amount=doctor_1.fee,
        status=PaymentStatusEnum.PAID,
        transactionId="TXN-0008",
        checkoutUrl="https://payos.vn/checkout/TXN-0008",
        qrCode="QR-CODE-TXN-0008",
        paidAt=datetime.combine(two_weeks_ago_tue, time(8, 30)),
    )
    appointments.append(appointment_8)
    payments.append(payment_8)

    three_weeks_ago_wed = monday_this_week - timedelta(days=19)
    appointment_9 = Appointment(
        patientProfile=profile_cuong,
        doctor=doctor_1,
        scheduledDate=three_weeks_ago_wed,
        scheduledTime=time(10, 0),
        status=AppointmentStatusEnum.COMPLETED,
        reason="Khám tổng quát định kỳ.",
    )
    payment_9 = Payment(
        appointment=appointment_9,
        amount=doctor_1.fee,
        status=PaymentStatusEnum.PAID,
        transactionId="TXN-0009",
        checkoutUrl="https://payos.vn/checkout/TXN-0009",
        qrCode="QR-CODE-TXN-0009",
        paidAt=datetime.combine(three_weeks_ago_wed, time(10, 0)),
    )
    appointments.append(appointment_9)
    payments.append(payment_9)

    # 8.10 Hạnh hủy lịch khám Da liễu, bác sĩ đang xử lý hoàn tiền (REFUND_PENDING)
    appointment_10 = Appointment(
        patientProfile=profile_hanh,
        doctor=doctor_4,
        scheduledDate=monday_this_week + timedelta(days=3),
        scheduledTime=time(15, 0),
        status=AppointmentStatusEnum.CANCELLED,
        reason="Khám da liễu.",
        cancelledByUser=doctor_user_4,
        cancelReason="Bác sĩ có lịch hội chẩn đột xuất.",
        cancelledAt=datetime.now(),
    )
    payment_10 = Payment(
        appointment=appointment_10,
        amount=doctor_4.fee,
        status=PaymentStatusEnum.REFUND_PENDING,
        transactionId="TXN-0010",
        checkoutUrl="https://payos.vn/checkout/TXN-0010",
        qrCode="QR-CODE-TXN-0010",
        paidAt=datetime.now() - timedelta(days=1),
    )
    appointments.append(appointment_10)
    payments.append(payment_10)

    # 8.11 Hạnh đặt lịch khám Nhi cho con nhưng thanh toán thất bại (FAILED)
    appointment_11 = Appointment(
        patientProfile=profile_con_hanh,
        doctor=doctor_3,
        scheduledDate=monday_this_week + timedelta(days=4),
        scheduledTime=time(9, 0),
        status=AppointmentStatusEnum.CONFIRMED,
        reason="Ho, sổ mũi 2 ngày.",
    )
    payment_11 = Payment(
        appointment=appointment_11,
        amount=doctor_3.fee,
        status=PaymentStatusEnum.FAILED,
        transactionId="TXN-0011",
        checkoutUrl="https://payos.vn/checkout/TXN-0011",
        qrCode="QR-CODE-TXN-0011",
        paidAt=None,
    )
    appointments.append(appointment_11)
    payments.append(payment_11)

    db.session.add_all(appointments)
    db.session.flush()
    db.session.add_all(payments)
    db.session.flush()

    # ---------------------------------------------------
    # 9. Review (UC_06) - chỉ cho Appointment đã COMPLETED
    # ---------------------------------------------------
    reviews = [
        Review(
            appointment=appointment_3,
            doctor=doctor_2,
            author=patient_user_2,
            rating=5,
            comment="Bác sĩ tận tâm, giải thích rõ ràng, rất hài lòng.",
            time=datetime.now(),
        ),
        Review(
            appointment=appointment_8,
            doctor=doctor_1,
            author=patient_user_1,
            rating=4,
            comment="Bác sĩ khám kỹ, tuy hơi phải chờ lâu.",
            time=datetime.now(),
        ),
        Review(
            appointment=appointment_9,
            doctor=doctor_1,
            author=patient_user_3,
            rating=5,
            comment="Rất chuyên nghiệp, tư vấn dễ hiểu, sẽ quay lại.",
            time=datetime.now(),
        ),
    ]
    db.session.add_all(reviews)

    # ---------------------------------------------------
    # 10. Notification
    # ---------------------------------------------------
    notifications = [
        Notification(
            user=patient_user_1,
            title="Đặt lịch thành công",
            body=f"Lịch khám với {doctor_user_1.name} vào {monday_this_week} 08:00 đã được xác nhận.",
            type=NotificationTypeEnum.APPOINTMENT,
            isRead=False,
        ),
        Notification(
            user=doctor_user_1,
            title="Có lịch hẹn mới",
            body=f"Bệnh nhân {profile_binh.name} đã đặt lịch khám lúc 08:00 ngày {monday_this_week}.",
            type=NotificationTypeEnum.APPOINTMENT,
            isRead=False,
        ),
        Notification(
            user=patient_user_1,
            title="Lịch hẹn đã được hủy",
            body=f"Cuộc hẹn ngày {appointment_4.scheduledDate} đã được hủy và hoàn phí 100%.",
            type=NotificationTypeEnum.APPOINTMENT,
            isRead=True,
        ),
        Notification(
            user=patient_user_2,
            title="Thanh toán thành công",
            body=f"Thanh toán cho lịch khám ngày {appointment_2.scheduledDate} đã thành công.",
            type=NotificationTypeEnum.PAYMENT,
            isRead=False,
        ),
        Notification(
            user=patient_user_3,
            title="Nhắc thanh toán",
            body=f"Lịch khám ngày {appointment_5.scheduledDate} với {doctor_user_4.name} chưa được thanh toán.",
            type=NotificationTypeEnum.PAYMENT,
            isRead=False,
        ),
        Notification(
            user=patient_user_4,
            title="Đang xử lý hoàn tiền",
            body=f"Yêu cầu hoàn tiền cho lịch khám ngày {appointment_10.scheduledDate} đang được xử lý.",
            type=NotificationTypeEnum.PAYMENT,
            isRead=False,
        ),
        Notification(
            user=patient_user_4,
            title="Thanh toán thất bại",
            body=f"Thanh toán cho lịch khám ngày {appointment_11.scheduledDate} không thành công, vui lòng thử lại.",
            type=NotificationTypeEnum.PAYMENT,
            isRead=False,
        ),
        Notification(
            user=admin,
            title="Chào mừng quản trị viên",
            body="Hệ thống Đặt lịch khám trực tuyến đã được khởi tạo thành công.",
            type=NotificationTypeEnum.SYSTEM,
            isRead=True,
        ),
    ]
    db.session.add_all(notifications)

    db.session.commit()

    # ---------------------------------------------------
    # Kiểm tra ràng buộc: mọi bệnh nhân đều có health profile
    # ---------------------------------------------------
    patients_without_profile = [
        u.username for u in User.query.filter_by(role=UserRoleEnum.PATIENT).all()
        if not u.healthProfiles
    ]
    if patients_without_profile:
        print(f"[CẢNH BÁO] Các bệnh nhân chưa có hồ sơ sức khỏe: {patients_without_profile}")
    else:
        print("Đã xác nhận: mọi bệnh nhân đều có ít nhất 1 PatientHealthProfile.")

    print("Đã seed dữ liệu mẫu thành công:")
    print(f"  - Users: {User.query.count()}")
    print(f"  - PatientHealthProfile: {PatientHealthProfile.query.count()}")
    print(f"  - DoctorProfile: {DoctorProfile.query.count()}")
    print(f"  - Specialization: {Specialization.query.count()}")
    print(f"  - WorkSchedule: {WorkSchedule.query.count()}")
    print(f"  - ChatbotSession: {ChatbotSession.query.count()}")
    print(f"  - ChatbotDoctorSuggestion: {ChatbotDoctorSuggestion.query.count()}")
    print(f"  - Appointment: {Appointment.query.count()}")
    print(f"  - Payment: {Payment.query.count()}")
    print(f"  - Review: {Review.query.count()}")
    print(f"  - Notification: {Notification.query.count()}")


if __name__ == "__main__":
    with app.app_context():
        seed()