"""
sample_data.py
Script seed dữ liệu mẫu cho Hệ thống Đặt lịch khám trực tuyến.

Chạy độc lập:
    python sample_data.py
"""

import sys
from datetime import date, time, datetime, timedelta
from bookingonline.models import dao
from bookingonline import db, app, utils
from bookingonline.models.models import *

# Console Windows (cmd/PowerShell) mặc định không dùng UTF-8 -> print tiếng Việt
# có dấu sẽ crash UnicodeEncodeError. Ép lại encoding stdout để chạy được trên
# mọi terminal.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

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
    spec_noi = Specialization(name="Nội tổng quát")
    spec_nhi = Specialization(name="Nhi khoa")
    spec_da_lieu = Specialization(name="Da liễu")
    spec_tim_mach = Specialization(name="Tim mạch")
    db.session.add_all([spec_noi, spec_nhi, spec_da_lieu, spec_tim_mach])
    db.session.flush()  # để có id trước khi tham chiếu bên dưới

    # ---------------------------------------------------
    # 3. Users: admin, doctors, patients
    # ---------------------------------------------------
    admin = User(
        name="Quản trị viên",
        username="admin",
        email="admin@clinic.vn",
        password=utils.hash_password("Admin@123"),
        role=UserRoleEnum.ADMIN,
        gender=GenderEnum.MALE,
        phone="0900000000",
    )

    doctor_user_1 = User(
        name="BS. Nguyễn Thị Hoa",
        username="d1",
        email="phuquy141105@gmail.com",
        password=utils.hash_password("Doctor@123"),
        role=UserRoleEnum.DOCTOR,
        gender=GenderEnum.FEMALE,
        phone="0901111111",
    )
    doctor_user_2 = User(
        name="BS. Trần Văn Nam",
        username="d2",
        email="phuquy141105@gmail.com",
        password=utils.hash_password("Doctor@123"),
        role=UserRoleEnum.DOCTOR,
        gender=GenderEnum.MALE,
        phone="0902222222",
    )
    doctor_user_3 = User(
        name="BS. Phạm Thuỳ Linh",
        username="d3",
        email="phuquy141105@gmail.com",
        password=utils.hash_password("Doctor@123"),
        role=UserRoleEnum.DOCTOR,
        gender=GenderEnum.FEMALE,
        phone="0903333333",
    )

    patient_user_1 = User(
        name="Nguyễn Văn Bình",
        username="p1",
        email="phuquy141105@gmail.com",
        password=utils.hash_password("Patient@123"),
        role=UserRoleEnum.PATIENT,
        gender=GenderEnum.MALE,
        phone="0911111111",
    )
    patient_user_2 = User(
        name="Trần Thị Mai",
        username="p2",
        email="phuquy141105@gmail.com",
        password=utils.hash_password("Patient@123"),
        role=UserRoleEnum.PATIENT,
        gender=GenderEnum.FEMALE,
        phone="0912222222",
    )

    db.session.add_all([
        admin, doctor_user_1, doctor_user_2, doctor_user_3,
        patient_user_1, patient_user_2,
    ])
    db.session.flush()

    # ---------------------------------------------------
    # 4. DoctorProfile (gán qua object "user"/"specialization", không cần tự set *Id)
    # ---------------------------------------------------
    doctor_1 = DoctorProfile(
        user=doctor_user_1,
        specialization=spec_noi,
        licenseNumber="BS-001-2015",
        experienceYrs=10,
        description="Chuyên khám và điều trị các bệnh lý nội tổng quát.",
        bio="Tốt nghiệp Đại học Y Dược TP.HCM, 10 năm kinh nghiệm.",
        totalReview=2,
        averageRating=4.5,
        avatarUrl="https://example.com/avatars/bs_hoa.jpg",
        fee=250000,  # thêm chi phí khám
    )

    doctor_2 = DoctorProfile(
        user=doctor_user_2,
        specialization=spec_tim_mach,
        licenseNumber="BS-002-2012",
        experienceYrs=13,
        description="Chuyên khoa Tim mạch, siêu âm tim, điện tâm đồ.",
        bio="13 năm kinh nghiệm tại các bệnh viện tuyến trung ương.",
        totalReview=1,
        averageRating=5.0,
        avatarUrl="https://example.com/avatars/bs_nam.jpg",
        fee=300000,  # thêm chi phí khám
    )

    doctor_3 = DoctorProfile(
        user=doctor_user_3,
        specialization=spec_nhi,
        licenseNumber="BS-003-2018",
        experienceYrs=7,
        description="Chuyên khám nhi, tư vấn dinh dưỡng trẻ em.",
        bio="7 năm kinh nghiệm khám nhi khoa.",
        totalReview=0,
        averageRating=0.0,
        avatarUrl="https://example.com/avatars/bs_linh.jpg",
        fee=200000,  # thêm chi phí khám
    )

    db.session.add_all([doctor_1, doctor_2, doctor_3])
    db.session.flush()

    # ---------------------------------------------------
    # 5. PatientHealthProfile
    #    - Bình có 1 hồ sơ cho chính mình
    #    - Mai có 2 hồ sơ: chính mình + đặt hộ cho con
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
    db.session.add_all([profile_binh, profile_mai, profile_con_mai])
    db.session.flush()

    # ---------------------------------------------------
    # 6. WorkSchedule cho tuần hiện tại
    # ---------------------------------------------------
    today = date.today()
    monday_this_week = today - timedelta(days=today.weekday())

    work_schedules = []
    for day_offset in range(6):  # Mon-Sat theo workingDays ở SystemConfig
        work_date = monday_this_week + timedelta(days=day_offset)
        for doctor in (doctor_1, doctor_2, doctor_3):
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

    slot_doctor1_mon_morning = next(
        ws for ws in work_schedules
        if ws.doctor is doctor_1
        and ws.workDate == monday_this_week
        and ws.session == WorkScheduleSessionEnum.MORNING
    )

    # ---------------------------------------------------
    # 7. ChatbotSession + ChatbotDoctorSuggestion (UC_03)
    # ---------------------------------------------------
    chatbot_session = ChatbotSession(
        user=patient_user_1,
        specialization=spec_noi,
        bookedDate=monday_this_week,
        queryText="Tôi bị đau bụng âm ỉ vùng thượng vị, kèm buồn nôn 2 ngày nay.",
        aiRequirements="Phân tích triệu chứng liên quan tiêu hóa / nội tổng quát.",
    )
    db.session.add(chatbot_session)
    db.session.flush()

    suggestion = ChatbotDoctorSuggestion(
        session=chatbot_session,
        doctor=doctor_1,
        availableDate=monday_this_week,
        startTime=time(8, 0),
        endTime=time(8, 30),
        reason="Triệu chứng phù hợp chuyên khoa Nội tổng quát.",
    )
    db.session.add(suggestion)
    db.session.flush()

    # ---------------------------------------------------
    # 8. Appointment (UC_01) - sinh từ gợi ý chatbot ở trên
    # ---------------------------------------------------
    appointment_1 = Appointment(
        patientProfile=profile_binh,
        doctor=doctor_1,
        workSchedule=slot_doctor1_mon_morning,
        chatbotSuggestion=suggestion,
        scheduledDate=monday_this_week,
        scheduledTime=time(8, 0),
        status=AppointmentStatusEnum.CONFIRMED,
        reason="Đau bụng âm ỉ vùng thượng vị, buồn nôn.",
    )
    db.session.add(appointment_1)
    db.session.flush()

    payment_1 = Payment(
        appointment=appointment_1,
        amount=doctor_1.fee,
        status=PaymentStatusEnum.PAID,
        transactionId="TXN-0001",
        checkoutUrl="https://payos.vn/checkout/TXN-0001",
        qrCode="QR-CODE-TXN-0001",
        paidAt=datetime.now(),
    )
    db.session.add(payment_1)

    # Appointment thứ 2: đặt hộ cho con của Mai, với bác sĩ Nhi khoa
    slot_doctor3 = next(
        ws for ws in work_schedules
        if ws.doctor is doctor_3
        and ws.workDate == monday_this_week
        and ws.session == WorkScheduleSessionEnum.AFTERNOON
    )
    appointment_2 = Appointment(
        patientProfile=profile_con_mai,
        doctor=doctor_3,
        workSchedule=slot_doctor3,
        scheduledDate=monday_this_week,
        scheduledTime=time(13, 30),
        status=AppointmentStatusEnum.CONFIRMED,
        reason="Khám định kỳ, tư vấn dinh dưỡng.",
    )
    db.session.add(appointment_2)
    db.session.flush()

    payment_2 = Payment(
        appointment=appointment_2,
        amount=doctor_2.fee,
        status=PaymentStatusEnum.PAID,
        transactionId="TXN-0002",
        checkoutUrl="https://payos.vn/checkout/TXN-0002",
        qrCode="QR-CODE-TXN-0002",
        paidAt=datetime.now(),
    )
    db.session.add(payment_2)

    # Appointment thứ 3: đã hoàn thành (tuần trước) -> đủ điều kiện đánh giá (UC_06)
    last_monday = monday_this_week - timedelta(days=7)
    appointment_3 = Appointment(
        patientProfile=profile_mai,
        doctor=doctor_2,
        scheduledDate=last_monday,
        scheduledTime=time(9, 0),
        status=AppointmentStatusEnum.COMPLETED,
        reason="Khám tim mạch định kỳ.",
    )
    db.session.add(appointment_3)
    db.session.flush()

    payment_3 = Payment(
        appointment=appointment_3,
        amount=doctor_3.fee,
        status=PaymentStatusEnum.PAID,
        transactionId="TXN-0003",
        checkoutUrl="https://payos.vn/checkout/TXN-0003",
        qrCode="QR-CODE-TXN-0003",
        paidAt=datetime.combine(last_monday, time(9, 0)),
    )
    db.session.add(payment_3)

    # Appointment thứ 4: đã bị bệnh nhân hủy (UC_02)
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
    db.session.add(appointment_4)
    db.session.flush()

    payment_4 = Payment(
        appointment=appointment_4,
        amount=doctor_2.fee,
        status=PaymentStatusEnum.REFUND,
        transactionId="TXN-0004",
        checkoutUrl="https://payos.vn/checkout/TXN-0004",
        qrCode="QR-CODE-TXN-0004",
        paidAt=datetime.now() - timedelta(days=1),
    )
    db.session.add(payment_4)

    # ---------------------------------------------------
    # 9. Review (UC_06) - cho appointment_3 đã Completed
    # ---------------------------------------------------
    review_1 = Review(
        appointment=appointment_3,
        doctor=doctor_2,
        author=patient_user_2,
        rating=5,
        comment="Bác sĩ tận tâm, giải thích rõ ràng, rất hài lòng.",
        time=datetime.now(),
    )
    db.session.add(review_1)

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
    ]
    db.session.add_all(notifications)

    db.session.commit()

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