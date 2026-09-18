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
        minimumBookingTime=45,
        minimumCancellationTime=180,
        workingDays="MONDAY,TUESDAY,WEDNESDAY,THURSDAY,FRIDAY,SATURDAY",
        morningStartTime=time(8, 0),
        morningEndTime=time(12, 0),
        afternoonStartTime=time(13, 30),
        afternoonEndTime=time(17, 30),
        maxAppointmentsPerDay=1,
        refundPercentagePatient=100,
        refundPercentageDoctor=100,
    )
    db.session.add(config)

    # ---------------------------------------------------
    # 2. Specialization
    # ---------------------------------------------------
    spec_tmh = Specialization(name="Tai Mũi Họng", icon="ear-listen",
                               description="Khám và điều trị các bệnh lý tai, mũi, họng.")
    spec_noi_tiet = Specialization(name="Nội tiết", icon="syringe",
                                    description="Khám, tầm soát và điều trị tiểu đường, tuyến giáp.")
    spec_co_xuong_khop = Specialization(name="Cơ xương khớp", icon="bone",
                                         description="Khám và điều trị các bệnh lý xương khớp, thoái hóa.")
    spec_mat = Specialization(name="Mắt", icon="eye",
                               description="Khám, đo thị lực và điều trị các bệnh lý về mắt.")
    db.session.add_all([spec_tmh, spec_noi_tiet, spec_co_xuong_khop, spec_mat])
    db.session.flush()  # để có id trước khi tham chiếu bên dưới

    # ---------------------------------------------------
    # 3. Users: admin, doctors, patients
    # ---------------------------------------------------
    admin = User(
        name="Đỗ Minh Quản",
        username="admin",
        email="admin@phongkham.vn",
        password="Admin@123",
        role=UserRoleEnum.ADMIN,
        gender=GenderEnum.MALE,
        phone="0900123456",
    )

    doctor_user_1 = User(
        name="BS. Vũ Thị Ngọc Lan",
        username="bs.lan",
        email="lan.vu@phongkham.vn",
        password="Doctor@123",
        role=UserRoleEnum.DOCTOR,
        gender=GenderEnum.FEMALE,
        phone="0905111222",
    )
    doctor_user_2 = User(
        name="BS. Hoàng Đức Thắng",
        username="bs.thang",
        email="thang.hoang@phongkham.vn",
        password="Doctor@123",
        role=UserRoleEnum.DOCTOR,
        gender=GenderEnum.MALE,
        phone="0905222333",
    )
    doctor_user_3 = User(
        name="BS. Đặng Thị Kim Yến",
        username="bs.yen",
        email="yen.dang@phongkham.vn",
        password="Doctor@123",
        role=UserRoleEnum.DOCTOR,
        gender=GenderEnum.FEMALE,
        phone="0905333444",
    )
    doctor_user_4 = User(
        name="BS. Ngô Bảo Long",
        username="bs.long",
        email="long.ngo@phongkham.vn",
        password="Doctor@123",
        role=UserRoleEnum.DOCTOR,
        gender=GenderEnum.MALE,
        phone="0905444555",
    )

    patient_user_1 = User(
        name="Trịnh Văn Phúc",
        username="phuc.trinh",
        email="phuc.trinh@gmail.com",
        password="Patient@123",
        role=UserRoleEnum.PATIENT,
        gender=GenderEnum.MALE,
        phone="0918111222",
        bank_bin="970422",
        bank_account_number="0325391105",
        bank_account_name="PHAM HOANG PHU QUY",
    )
    patient_user_2 = User(
        name="Bùi Thị Ngọc Anh",
        username="ngocanh.bui",
        email="ngocanh.bui@gmail.com",
        password="Patient@123",
        role=UserRoleEnum.PATIENT,
        gender=GenderEnum.FEMALE,
        phone="0918222333",
        bank_bin="970422",
        bank_account_number="0325391105",
        bank_account_name="PHAM HOANG PHU QUY",
    )
    patient_user_3 = User(
        name="Dương Quốc Việt",
        username="viet.duong",
        email="viet.duong@gmail.com",
        password="Patient@123",
        role=UserRoleEnum.PATIENT,
        gender=GenderEnum.MALE,
        phone="0918333444",
        bank_bin="970422",
        bank_account_number="0325391105",
        bank_account_name="PHAM HOANG PHU QUY",
    )
    patient_user_4 = User(
        name="Lâm Thị Thu Trang",
        username="trang.lam",
        email="trang.lam@gmail.com",
        password="Patient@123",
        role=UserRoleEnum.PATIENT,
        gender=GenderEnum.FEMALE,
        phone="0918444555",
        bank_bin="970422",
        bank_account_number="0325391105",
        bank_account_name="PHAM HOANG PHU QUY",
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
        specialization=spec_tmh,
        licenseNumber="BS-TMH-2014",
        experienceYrs=12,
        description="Chuyên khám và điều trị viêm xoang, viêm họng, viêm tai giữa.",
        bio="Tốt nghiệp Đại học Y Hà Nội, 12 năm kinh nghiệm Tai Mũi Họng.",
        room="Phòng 102, Lầu 1",
        totalReview=2,
        averageRating=4.5,
        avatarUrl="https://example.com/avatars/bs_lan.jpg",
        fee=230000,
    )
    doctor_2 = DoctorProfile(
        user=doctor_user_2,
        specialization=spec_noi_tiet,
        licenseNumber="BS-NT-2011",
        experienceYrs=14,
        description="Chuyên khoa Nội tiết, kiểm soát đường huyết, bệnh lý tuyến giáp.",
        bio="14 năm kinh nghiệm tại các bệnh viện tuyến trung ương.",
        room="Phòng 203, Lầu 2",
        totalReview=1,
        averageRating=5.0,
        avatarUrl="https://example.com/avatars/bs_thang.jpg",
        fee=280000,
    )
    doctor_3 = DoctorProfile(
        user=doctor_user_3,
        specialization=spec_co_xuong_khop,
        licenseNumber="BS-CXK-2017",
        experienceYrs=8,
        description="Chuyên khám và điều trị đau lưng, thoái hóa khớp, loãng xương.",
        bio="8 năm kinh nghiệm khám cơ xương khớp.",
        room="Phòng 106, Lầu 1",
        totalReview=0,
        averageRating=0.0,
        avatarUrl="https://example.com/avatars/bs_yen.jpg",
        fee=210000,
    )
    doctor_4 = DoctorProfile(
        user=doctor_user_4,
        specialization=spec_mat,
        licenseNumber="BS-MAT-2019",
        experienceYrs=6,
        description="Chuyên khám khúc xạ, đo thị lực, điều trị viêm kết mạc.",
        bio="6 năm kinh nghiệm khám mắt tại các phòng khám tư nhân.",
        room="Phòng 302, Lầu 3",
        totalReview=0,
        averageRating=0.0,
        avatarUrl="https://example.com/avatars/bs_long.jpg",
        fee=190000,
    )

    db.session.add_all([doctor_1, doctor_2, doctor_3, doctor_4])
    db.session.flush()

    # ---------------------------------------------------
    # 5. PatientHealthProfile
    #    -> MỌI bệnh nhân (role PATIENT) đều có ít nhất 1 hồ sơ sức khỏe.
    #    - Phúc: 1 hồ sơ cho chính mình
    #    - Ngọc Anh: 2 hồ sơ (chính mình + con)
    #    - Việt: 1 hồ sơ cho chính mình
    #    - Thu Trang: 2 hồ sơ (chính mình + con)
    # ---------------------------------------------------
    profile_phuc = PatientHealthProfile(
        owner=patient_user_1,
        name="Trịnh Văn Phúc",
        phone="0918111222",
        gender=GenderEnum.MALE,
        dateOfBirth=date(1991, 6, 12),
        address="10 Hai Bà Trưng, Quận 1, TP.HCM",
    )
    profile_ngocanh = PatientHealthProfile(
        owner=patient_user_2,
        name="Bùi Thị Ngọc Anh",
        phone="0918222333",
        gender=GenderEnum.FEMALE,
        dateOfBirth=date(1989, 4, 22),
        address="56 Nguyễn Đình Chiểu, Quận 3, TP.HCM",
    )
    profile_con_ngocanh = PatientHealthProfile(
        owner=patient_user_2,  # đặt lịch hộ: vẫn thuộc tài khoản của Ngọc Anh
        name="Bùi Gia Hân",
        phone="0918222333",
        gender=GenderEnum.FEMALE,
        dateOfBirth=date(2018, 9, 5),
        address="56 Nguyễn Đình Chiểu, Quận 3, TP.HCM",
    )
    profile_viet = PatientHealthProfile(
        owner=patient_user_3,
        name="Dương Quốc Việt",
        phone="0918333444",
        gender=GenderEnum.MALE,
        dateOfBirth=date(1996, 1, 30),
        address="89 Cách Mạng Tháng 8, Quận 10, TP.HCM",
    )
    profile_trang = PatientHealthProfile(
        owner=patient_user_4,
        name="Lâm Thị Thu Trang",
        phone="0918444555",
        gender=GenderEnum.FEMALE,
        dateOfBirth=date(1993, 12, 18),
        address="34 Điện Biên Phủ, Bình Thạnh, TP.HCM",
    )
    profile_con_trang = PatientHealthProfile(
        owner=patient_user_4,  # đặt lịch hộ cho con
        name="Lâm Gia Bảo",
        phone="0918444555",
        gender=GenderEnum.MALE,
        dateOfBirth=date(2021, 3, 8),
        address="34 Điện Biên Phủ, Bình Thạnh, TP.HCM",
    )
    db.session.add_all([
        profile_phuc, profile_ngocanh, profile_con_ngocanh,
        profile_viet, profile_trang, profile_con_trang,
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
                startTime=time(8, 0),
                endTime=time(12, 0),
                isAvailable=True,
            ))
            work_schedules.append(WorkSchedule(
                doctor=doctor,
                workDate=work_date,
                session=WorkScheduleSessionEnum.AFTERNOON,
                startTime=time(13, 30),
                endTime=time(17, 30),
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
        specialization=spec_tmh,
        bookedDate=monday_this_week,
        queryText="Tôi bị nghẹt mũi, đau họng và ù tai 3 ngày nay.",
        aiRequirements="Phân tích triệu chứng liên quan tai mũi họng.",
    )
    chatbot_session_2 = ChatbotSession(
        user=patient_user_3,
        specialization=spec_mat,
        bookedDate=tuesday_this_week,
        queryText="Mắt tôi mờ dần, hay chảy nước mắt và cộm khi nhìn màn hình lâu.",
        aiRequirements="Phân tích triệu chứng liên quan mắt / khúc xạ.",
    )
    db.session.add_all([chatbot_session_1, chatbot_session_2])
    db.session.flush()

    suggestion_1 = ChatbotDoctorSuggestion(
        session=chatbot_session_1,
        doctor=doctor_1,
        availableDate=monday_this_week,
        startTime=time(8, 30),
        endTime=time(9, 0),
        reason="Triệu chứng phù hợp chuyên khoa Tai Mũi Họng.",
    )
    suggestion_2 = ChatbotDoctorSuggestion(
        session=chatbot_session_2,
        doctor=doctor_4,
        availableDate=tuesday_this_week,
        startTime=time(8, 30),
        endTime=time(9, 0),
        reason="Triệu chứng phù hợp chuyên khoa Mắt.",
    )
    db.session.add_all([suggestion_1, suggestion_2])
    db.session.flush()

    # ---------------------------------------------------
    # 8. Appointment (UC_01) + Payment
    # ---------------------------------------------------
    appointments = []
    payments = []

    # 8.1 Sinh từ gợi ý chatbot - Phúc khám TMH với BS. Lan (CONFIRMED, đã thanh toán)
    appointment_1 = Appointment(
        patientProfile=profile_phuc,
        doctor=doctor_1,
        workSchedule=slot_doctor1_mon_morning,
        chatbotSuggestion=suggestion_1,
        scheduledDate=monday_this_week,
        scheduledTime=time(8, 30),
        status=AppointmentStatusEnum.CONFIRMED,
        reason="Nghẹt mũi, đau họng, ù tai.",
    )
    payment_1 = Payment(
        appointment=appointment_1,
        amount=doctor_1.fee,
        status=PaymentStatusEnum.PAID,
        transactionId="TXN-1001",
        checkoutUrl="https://payos.vn/checkout/TXN-1001",
        qrCode="QR-CODE-TXN-1001",
        paidAt=datetime.now(),
    )
    appointments.append(appointment_1)
    payments.append(payment_1)

    # 8.2 Ngọc Anh đặt hộ cho con (Hân) khám Cơ xương khớp với BS. Yến (CONFIRMED, đã thanh toán)
    appointment_2 = Appointment(
        patientProfile=profile_con_ngocanh,
        doctor=doctor_3,
        workSchedule=slot_doctor3_mon_afternoon,
        scheduledDate=monday_this_week,
        scheduledTime=time(14, 0),
        status=AppointmentStatusEnum.CONFIRMED,
        reason="Đau nhức chân sau khi vận động mạnh.",
    )
    payment_2 = Payment(
        appointment=appointment_2,
        amount=doctor_3.fee,
        status=PaymentStatusEnum.PAID,
        transactionId="TXN-1002",
        checkoutUrl="https://payos.vn/checkout/TXN-1002",
        qrCode="QR-CODE-TXN-1002",
        paidAt=datetime.now(),
    )
    appointments.append(appointment_2)
    payments.append(payment_2)

    # 8.3 Ngọc Anh khám Nội tiết với BS. Thắng - đã hoàn thành tuần trước (đủ điều kiện đánh giá UC_06)
    last_monday = monday_this_week - timedelta(days=7)
    appointment_3 = Appointment(
        patientProfile=profile_ngocanh,
        doctor=doctor_2,
        scheduledDate=last_monday,
        scheduledTime=time(9, 30),
        status=AppointmentStatusEnum.COMPLETED,
        reason="Khám nội tiết, kiểm tra đường huyết định kỳ.",
    )
    payment_3 = Payment(
        appointment=appointment_3,
        amount=doctor_2.fee,
        status=PaymentStatusEnum.PAID,
        transactionId="TXN-1003",
        checkoutUrl="https://payos.vn/checkout/TXN-1003",
        qrCode="QR-CODE-TXN-1003",
        paidAt=datetime.combine(last_monday, time(9, 30)),
    )
    appointments.append(appointment_3)
    payments.append(payment_3)

    # 8.4 Phúc hủy lịch khám Nội tiết với BS. Thắng (CANCELLED bởi bệnh nhân, hoàn phí 100%)
    appointment_4 = Appointment(
        patientProfile=profile_phuc,
        doctor=doctor_2,
        scheduledDate=monday_this_week + timedelta(days=2),
        scheduledTime=time(10, 30),
        status=AppointmentStatusEnum.CANCELLED,
        reason="Khám nội tiết.",
        cancelledByUser=patient_user_1,
        cancelReason="Bận việc đột xuất, không thể đến khám.",
        cancelledAt=datetime.now(),
    )
    payment_4 = Payment(
        appointment=appointment_4,
        amount=doctor_2.fee,
        status=PaymentStatusEnum.REFUND,
        transactionId="TXN-1004",
        checkoutUrl="https://payos.vn/checkout/TXN-1004",
        qrCode="QR-CODE-TXN-1004",
        paidAt=datetime.now() - timedelta(days=1),
        # Bệnh nhân hủy sớm (đủ điều kiện hoàn 100%) -> đã hoàn tiền xong.
        refundPercent=100,
        refundAmount=doctor_2.fee,
        payoutId="PAYOUT-DEMO-TXN1004",
    )
    appointments.append(appointment_4)
    payments.append(payment_4)

    # 8.5 Sinh từ gợi ý chatbot - Việt khám Mắt với BS. Long (CONFIRMED, chưa thanh toán)
    appointment_5 = Appointment(
        patientProfile=profile_viet,
        doctor=doctor_4,
        workSchedule=slot_doctor4_tue_morning,
        chatbotSuggestion=suggestion_2,
        scheduledDate=tuesday_this_week,
        scheduledTime=time(8, 30),
        status=AppointmentStatusEnum.CONFIRMED,
        reason="Mắt mờ dần, cộm và chảy nước mắt.",
    )
    payment_5 = Payment(
        appointment=appointment_5,
        amount=doctor_4.fee,
        status=PaymentStatusEnum.PENDING,
        transactionId="TXN-1005",
        checkoutUrl="https://payos.vn/checkout/TXN-1005",
        qrCode="QR-CODE-TXN-1005",
        paidAt=None,
    )
    appointments.append(appointment_5)
    payments.append(payment_5)

    # 8.6 Thu Trang khám TMH với BS. Lan nhưng KHÔNG đến khám (NO_SHOW), đã thanh toán trước, không hoàn phí
    last_friday = monday_this_week - timedelta(days=3)
    appointment_6 = Appointment(
        patientProfile=profile_trang,
        doctor=doctor_1,
        scheduledDate=last_friday,
        scheduledTime=time(10, 0),
        status=AppointmentStatusEnum.NO_SHOW,
        reason="Viêm họng, khàn tiếng kéo dài.",
    )
    payment_6 = Payment(
        appointment=appointment_6,
        amount=doctor_1.fee,
        status=PaymentStatusEnum.PAID,
        transactionId="TXN-1006",
        checkoutUrl="https://payos.vn/checkout/TXN-1006",
        qrCode="QR-CODE-TXN-1006",
        paidAt=datetime.combine(last_friday, time(10, 0)) - timedelta(hours=2),
    )
    appointments.append(appointment_6)
    payments.append(payment_6)

    # 8.7 Con của Thu Trang (Bảo) khám Cơ xương khớp với BS. Yến - đã hoàn thành, chưa đánh giá
    two_weeks_ago_wed = monday_this_week - timedelta(days=12)
    appointment_7 = Appointment(
        patientProfile=profile_con_trang,
        doctor=doctor_3,
        scheduledDate=two_weeks_ago_wed,
        scheduledTime=time(15, 0),
        status=AppointmentStatusEnum.COMPLETED,
        reason="Khám định kỳ, theo dõi phát triển xương khớp.",
    )
    payment_7 = Payment(
        appointment=appointment_7,
        amount=doctor_3.fee,
        status=PaymentStatusEnum.PAID,
        transactionId="TXN-1007",
        checkoutUrl="https://payos.vn/checkout/TXN-1007",
        qrCode="QR-CODE-TXN-1007",
        paidAt=datetime.combine(two_weeks_ago_wed, time(15, 0)),
    )
    appointments.append(appointment_7)
    payments.append(payment_7)

    # 8.8 & 8.9: Phúc và Việt từng khám TMH với BS. Lan - đã hoàn thành + đã đánh giá
    # (để dữ liệu review khớp với totalReview=2, averageRating=4.5 của doctor_1)
    two_weeks_ago_tue = monday_this_week - timedelta(days=13)
    appointment_8 = Appointment(
        patientProfile=profile_phuc,
        doctor=doctor_1,
        scheduledDate=two_weeks_ago_tue,
        scheduledTime=time(9, 0),
        status=AppointmentStatusEnum.COMPLETED,
        reason="Viêm xoang tái khám.",
    )
    payment_8 = Payment(
        appointment=appointment_8,
        amount=doctor_1.fee,
        status=PaymentStatusEnum.PAID,
        transactionId="TXN-1008",
        checkoutUrl="https://payos.vn/checkout/TXN-1008",
        qrCode="QR-CODE-TXN-1008",
        paidAt=datetime.combine(two_weeks_ago_tue, time(9, 0)),
    )
    appointments.append(appointment_8)
    payments.append(payment_8)

    three_weeks_ago_wed = monday_this_week - timedelta(days=19)
    appointment_9 = Appointment(
        patientProfile=profile_viet,
        doctor=doctor_1,
        scheduledDate=three_weeks_ago_wed,
        scheduledTime=time(11, 0),
        status=AppointmentStatusEnum.COMPLETED,
        reason="Khám tổng quát tai mũi họng định kỳ.",
    )
    payment_9 = Payment(
        appointment=appointment_9,
        amount=doctor_1.fee,
        status=PaymentStatusEnum.PAID,
        transactionId="TXN-1009",
        checkoutUrl="https://payos.vn/checkout/TXN-1009",
        qrCode="QR-CODE-TXN-1009",
        paidAt=datetime.combine(three_weeks_ago_wed, time(11, 0)),
    )
    appointments.append(appointment_9)
    payments.append(payment_9)

    # 8.10 Thu Trang hủy lịch khám Mắt, bác sĩ đang xử lý hoàn tiền (REFUND_PENDING)
    appointment_10 = Appointment(
        patientProfile=profile_trang,
        doctor=doctor_4,
        scheduledDate=monday_this_week + timedelta(days=3),
        scheduledTime=time(16, 0),
        status=AppointmentStatusEnum.CANCELLED,
        reason="Khám mắt.",
        cancelledByUser=doctor_user_4,
        cancelReason="Bác sĩ có lịch hội chẩn đột xuất.",
        cancelledAt=datetime.now(),
    )
    payment_10 = Payment(
        appointment=appointment_10,
        amount=doctor_4.fee,
        status=PaymentStatusEnum.REFUND_PENDING,
        transactionId="TXN-1010",
        checkoutUrl="https://payos.vn/checkout/TXN-1010",
        qrCode="QR-CODE-TXN-1010",
        paidAt=datetime.now() - timedelta(days=1),
        # Bác sĩ hủy -> luôn hoàn 100%. payoutId đã có sẵn (đã tạo lệnh chi
        # PayOS) nhưng CHƯA được Celery xác nhận -> dùng để test ngay
        # task check_pending_refunds() mà không cần thao tác hủy qua UI.
        refundPercent=100,
        refundAmount=doctor_4.fee,
        payoutId="PAYOUT-DEMO-TXN1010",
    )
    appointments.append(appointment_10)
    payments.append(payment_10)

    # 8.11 Thu Trang đặt lịch khám Cơ xương khớp cho con nhưng thanh toán thất bại (FAILED)
    appointment_11 = Appointment(
        patientProfile=profile_con_trang,
        doctor=doctor_3,
        scheduledDate=monday_this_week + timedelta(days=4),
        scheduledTime=time(9, 30),
        status=AppointmentStatusEnum.CONFIRMED,
        reason="Kêu đau khớp gối khi chạy nhảy.",
    )
    payment_11 = Payment(
        appointment=appointment_11,
        amount=doctor_3.fee,
        status=PaymentStatusEnum.FAILED,
        transactionId="TXN-1011",
        checkoutUrl="https://payos.vn/checkout/TXN-1011",
        qrCode="QR-CODE-TXN-1011",
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
            body=f"Lịch khám với {doctor_user_1.name} vào {monday_this_week} 08:30 đã được xác nhận.",
            type=NotificationTypeEnum.APPOINTMENT,
            isRead=False,
        ),
        Notification(
            user=doctor_user_1,
            title="Có lịch hẹn mới",
            body=f"Bệnh nhân {profile_phuc.name} đã đặt lịch khám lúc 08:30 ngày {monday_this_week}.",
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

    print("Đã seed dữ liệu mẫu mới thành công:")
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