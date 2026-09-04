from bookingonline import db, app
from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime, Date, Time, Boolean, Enum, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as ExtEnum
from flask_login import UserMixin
import json

class Base(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)
    createdAt = Column(DateTime, default=datetime.now)
    updatedAt = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    def __str__(self):
        return getattr(self, "name", None) or f"{self.__class__.__name__}#{self.id}"

class GenderEnum(ExtEnum):
    MALE = "MALE"
    FEMALE = "FEMALE"

class UserRoleEnum(ExtEnum):
    ADMIN = "ADMIN"
    PATIENT = "PATIENT"
    DOCTOR = "DOCTOR"

class AppointmentStatusEnum(ExtEnum):
    CONFIRMED = "CONFIRMED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"

class PaymentStatusEnum(ExtEnum):
    PENDING = "PENDING"
    PAID = "PAID"
    REFUND_PENDING = "REFUND_PENDING"
    REFUND = "REFUND"
    FAILED = "FAILED"

class NotificationTypeEnum(ExtEnum):
    SYSTEM = "SYSTEM"
    PAYMENT = "PAYMENT"
    APPOINTMENT = "APPOINTMENT"

class WorkScheduleSessionEnum(ExtEnum):
    MORNING = "MORNING"
    AFTERNOON = "AFTERNOON"

class User(Base, UserMixin):
    name = Column(String(150), nullable=False)
    username=Column(String(150), nullable=False)
    email = Column(String(120), nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(Enum(UserRoleEnum), default=UserRoleEnum.PATIENT, nullable=False)
    gender = Column(Enum(GenderEnum))
    phone = Column(String(20))
    active = Column(Boolean, default=True)
    healthProfiles = relationship("PatientHealthProfile", backref="owner")
    doctorProfile = relationship("DoctorProfile", backref="user", uselist=False)
    notifications = relationship("Notification", backref="user")
    chatbotSessions = relationship("ChatbotSession", backref="user")
    reviewsWritten = relationship("Review", backref="author")
    cancelledAppointments = relationship("Appointment", backref="cancelledByUser")


class Specialization(Base):
    name = Column(String(120), unique=True, nullable=False)
    doctors = relationship("DoctorProfile", backref="specialization")
    chatbotSessions = relationship("ChatbotSession", backref="specialization")

class PatientHealthProfile(Base):
    name = Column(String(120), nullable=False)
    phone = Column(String(20), nullable=False)
    gender = Column(Enum(GenderEnum))
    dateOfBirth = Column(Date)
    address = Column(String(255))
    userId = Column(Integer, ForeignKey(User.id), nullable=False)
    appointments = relationship("Appointment", backref="patientProfile")

class DoctorProfile(Base):
    licenseNumber = Column(String(50), nullable=False)
    experienceYrs = Column(Integer, default=0)
    description = Column(Text)
    fee = db.Column(db.Float, default=200000)
    bio = Column(Text)
    totalReview = Column(Integer, default=0)
    averageRating = Column(Float, default=0.0)
    avatarUrl = Column(String(255))
    userId = Column(Integer, ForeignKey(User.id), unique=True, nullable=False)
    specializationId = Column(Integer, ForeignKey(Specialization.id), nullable=False)
    workSchedules = relationship("WorkSchedule", backref="doctor")
    appointments = relationship("Appointment", backref="doctor")
    reviews = relationship("Review", backref="doctor")
    suggestions = relationship("ChatbotDoctorSuggestion", backref="doctor")

class WorkSchedule(Base):
    workDate = Column(Date, nullable=False)
    session = Column(Enum(WorkScheduleSessionEnum), nullable=False)
    startTime = Column(Time, nullable=False)
    endTime = Column(Time, nullable=False)
    isAvailable = Column(Boolean, default=True)
    doctorId = Column(Integer, ForeignKey(DoctorProfile.id), nullable=False)
    appointments = relationship("Appointment", backref="workSchedule")

class ChatbotSession(Base):
    bookedDate = Column(Date)
    queryText = Column(Text)
    aiRequirements = Column(Text)
    userId = Column(Integer, ForeignKey(User.id), nullable=False)
    specializationId = Column(Integer, ForeignKey(Specialization.id))
    suggestions = relationship("ChatbotDoctorSuggestion", backref="session")

class ChatbotDoctorSuggestion(Base):
    availableDate = Column(Date, nullable=False)
    startTime = Column(Time, nullable=False)
    endTime = Column(Time, nullable=False)
    reason = Column(Text)
    sessionId = Column(Integer, ForeignKey(ChatbotSession.id), nullable=False)
    doctorId = Column(Integer, ForeignKey(DoctorProfile.id), nullable=False)
    resultingAppointment = relationship("Appointment", backref="chatbotSuggestion", uselist=False)

class Appointment(Base):
    scheduledDate = Column(Date, nullable=False)
    scheduledTime = Column(Time, nullable=False)
    status = Column(Enum(AppointmentStatusEnum), default=AppointmentStatusEnum.CONFIRMED, nullable=False)
    reason = Column(Text)
    cancelReason = Column(Text)
    cancelledAt = Column(DateTime)
    patientProfileId = Column(Integer, ForeignKey(PatientHealthProfile.id), nullable=False)
    doctorId = Column(Integer, ForeignKey(DoctorProfile.id), nullable=False)
    workScheduleId = Column(Integer, ForeignKey(WorkSchedule.id))
    chatbotSuggestionId = Column(Integer, ForeignKey(ChatbotDoctorSuggestion.id))
    cancelledByUserId = Column(Integer, ForeignKey(User.id))
    payment = relationship("Payment", backref="appointment", uselist=False)
    review = relationship("Review", backref="appointment", uselist=False)

class Payment(Base):
    amount = Column(Float, nullable=False)
    status = Column(Enum(PaymentStatusEnum), default=PaymentStatusEnum.PENDING, nullable=False)
    transactionId = Column(String(100))
    checkoutUrl = Column(String(255))
    qrCode = Column(String(255))
    paidAt = Column(DateTime)
    appointmentId = Column(Integer, ForeignKey(Appointment.id), unique=True, nullable=False)

class Review(Base):
    rating = Column(Integer, nullable=False)
    comment = Column(Text)
    time = Column(DateTime, default=datetime.now)
    appointmentId = Column(Integer, ForeignKey(Appointment.id), unique=True, nullable=False)
    doctorId = Column(Integer, ForeignKey(DoctorProfile.id), nullable=False)
    authorId = Column(Integer, ForeignKey(User.id), nullable=False)  # bệnh nhân viết đánh giá

class Notification(Base):
    title = Column(String(200), nullable=False)
    body = Column(Text)
    type = Column(Enum(NotificationTypeEnum), nullable=False)
    isRead = Column(Boolean, default=False)
    userId = Column(Integer, ForeignKey(User.id), nullable=False)

class SystemConfig(Base):
    minimumBookingTime = Column(Integer, default=60)
    minimumCancellationTime = Column(Integer, default=120)
    workingDays = Column(String(100), default="MONDAY,TUESDAY,WEDNESDAY,THURSDAY,FRIDAY")
    morningStartTime = Column(Time, nullable=False)
    morningEndTime = Column(Time, nullable=False)
    afternoonStartTime = Column(Time, nullable=False)
    afternoonEndTime = Column(Time, nullable=False)
    maxAppointmentsPerDay = Column(Integer, default=1)
    refundPercentagePatient = Column(Integer, default=100)
    refundPercentageDoctor = Column(Integer, default=100)
    def workingDaysList(self):
        return [d.strip() for d in self.workingDays.split(",") if d.strip()]
if __name__ == "__main__":
    with app.app_context():
        db.create_all()