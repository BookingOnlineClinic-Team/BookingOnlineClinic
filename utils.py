import os
import io
import base64
from datetime import datetime, timedelta, date, time as dtime
from flask import render_template, url_for
from flask_mail import Mail, Message
from payos import PayOS
from payos.types import CreatePaymentLinkRequest
from bookingonline import app
from bookingonline.models import dao
from bookingonline.models.models import (NotificationTypeEnum, WorkSchedule, WorkScheduleSessionEnum)
from bookingonline import db
import qrcode

mail = Mail(app)
payos_client = PayOS(client_id=os.environ.get("PAYOS_CLIENT_ID"),api_key=os.environ.get("PAYOS_API_KEY"),checksum_key=os.environ.get("PAYOS_CHECKSUM_KEY"))


def create_payos_payment_link(payment):
    appointment = payment.appointment
    order_code = int(datetime.now().timestamp())
    description = f"Kham {appointment.doctor.user.name}"[:25]
    payment_data = CreatePaymentLinkRequest(
        order_code=order_code,
        amount=int(payment.amount),
        description=description,
        return_url=url_for("payment_status", payment_id=payment.id, _external=True),
        cancel_url=url_for("payment_status", payment_id=payment.id, _external=True),
    )
    response = payos_client.payment_requests.create(payment_data=payment_data)
    checkout_url = getattr(response, "checkout_url", None) or getattr(response, "checkoutUrl", None)
    qr_code = getattr(response, "qr_code", None) or getattr(response, "qrCode", None)
    return order_code, checkout_url, qr_code

def get_payos_payment_status(order_code):
    try:
        info = payos_client.payment_requests.get(order_code)
    except Exception as e:
        app.logger.warning(f"Không lấy được trạng thái PayOS cho {order_code}: {e}")
        return None
    return getattr(info, "status", None)

def verify_payos_webhook(raw_body):
    try:
        return payos_client.webhooks.verify(raw_body)
    except Exception as e:
        app.logger.warning(f"Webhook PayOS không hợp lệ: {e}")
        return None


def generate_qr_image_data_uri(qr_content: str):
    if not qr_content:
        return None
    try:
        img = qrcode.make(qr_content, box_size=8, border=2)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        return f"data:image/png;base64,{b64}"
    except Exception as e:
        app.logger.warning(f"Không sinh được ảnh QR: {e}")
        return None

def send_appointment_confirmation_email(appointment):
    if not app.config.get("MAIL_USERNAME"):
        app.logger.warning("MAIL_USERNAME chưa được cấu hình, bỏ qua gửi email")
        return
    html_content = render_template(
        "email_appointment_confirm.html",
        appointment=appointment,
        patient_name=appointment.patientProfile.name,
        doctor_name=appointment.doctor.user.name,
        specialization_name=appointment.doctor.specialization.name,
        scheduled_date=appointment.scheduledDate.strftime("%d/%m/%Y"),
        scheduled_time=appointment.scheduledTime.strftime("%H:%M"),
        room=appointment.doctor.room,
        fee=f"{int(appointment.doctor.fee):,}".replace(",", ".") + " đ",
        reason=appointment.reason,
        appointment_link=url_for(
            "appointment_success", appointment_id=appointment.id, _external=True
        ),
    )
    try:
        msg = Message(
            subject="[OU Clinic] Xác nhận lịch khám thành công",
            recipients=[appointment.patientProfile.owner.email],
            html=html_content,
        )
        mail.send(msg)
    except Exception as e:
        app.logger.warning(f"Gửi email xác nhận thất bại: {e}")


def notify_appointment_confirmed(appointment):
    dao.create_notification(
        user=appointment.patientProfile.owner,
        title="Đặt lịch thành công",
        body=(f"Lịch khám với {appointment.doctor.user.name} vào "
              f"{appointment.scheduledDate.strftime('%d/%m/%Y')} lúc "
              f"{appointment.scheduledTime.strftime('%H:%M')} đã được xác nhận."),
        ntype=NotificationTypeEnum.APPOINTMENT,
    )
    if appointment.doctor.user:
        dao.create_notification(
            user=appointment.doctor.user,
            title="Có lịch hẹn mới",
            body=(f"Bệnh nhân {appointment.patientProfile.name} đã đặt lịch khám lúc "
                  f"{appointment.scheduledTime.strftime('%H:%M')} ngày "
                  f"{appointment.scheduledDate.strftime('%d/%m/%Y')}."),
            ntype=NotificationTypeEnum.APPOINTMENT,
        )


def finalize_paid_appointment(payment):
    dao.confirm_payment_paid(payment)
    appointment = payment.appointment
    send_appointment_confirmation_email(appointment)
    notify_appointment_confirmed(appointment)

def _generate_slots(start_time: dtime, end_time: dtime, slot_minutes=30):
    slots = []
    cur = datetime.combine(date.today(), start_time)
    end = datetime.combine(date.today(), end_time)
    while cur + timedelta(minutes=slot_minutes) <= end:
        slots.append((cur.time(), (cur + timedelta(minutes=slot_minutes)).time()))
        cur += timedelta(minutes=slot_minutes)
    return slots


def generate_work_schedules_for_doctor(doctor, start_date: date, end_date: date, slot_minutes=30):
    config = dao.get_system_config()
    working_days = set(config.workingDaysList())
    day_name_map = {
        0: "MONDAY", 1: "TUESDAY", 2: "WEDNESDAY", 3: "THURSDAY",
        4: "FRIDAY", 5: "SATURDAY", 6: "SUNDAY",
    }

    morning_slots = _generate_slots(config.morningStartTime, config.morningEndTime, slot_minutes)
    print(morning_slots)
    afternoon_slots = _generate_slots(config.afternoonStartTime, config.afternoonEndTime, slot_minutes)
    print(afternoon_slots)
    created = 0
    cur_date = start_date
    while cur_date <= end_date:
        if day_name_map[cur_date.weekday()] in working_days:
            for session, slots in ((WorkScheduleSessionEnum.MORNING, morning_slots),
                                    (WorkScheduleSessionEnum.AFTERNOON, afternoon_slots)):
                for start_t, end_t in slots:
                    exists = WorkSchedule.query.filter_by(doctorId=doctor.id, workDate=cur_date, startTime=start_t).first()
                    if exists:
                        continue
                    ws = WorkSchedule(workDate=cur_date, session=session,startTime=start_t, endTime=end_t,isAvailable=True, doctor=doctor,)
                    db.session.add(ws)
                    created += 1
        cur_date += timedelta(days=1)
    db.session.commit()
    return created
