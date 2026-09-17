import os
import tempfile

_fd, _path = tempfile.mkstemp(suffix=".sqlite3")
os.environ["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + _path.replace("\\", "/")
os.environ.setdefault("PAYOS_CLIENT_ID", "test-client-id")
os.environ.setdefault("PAYOS_API_KEY", "test-api-key")
os.environ.setdefault("PAYOS_CHECKSUM_KEY", "test-checksum-key")

import pytest
from datetime import time as dtime

from bookingonline import app as flask_app, db
from bookingonline.models import dao
from bookingonline.models.models import (
    User, UserRoleEnum, GenderEnum, Specialization, DoctorProfile, SystemConfig,
)
import bookingonline.index

flask_app.config["TESTING"] = True
flask_app.config["WTF_CSRF_ENABLED"] = False


@pytest.fixture(scope="session", autouse=True)
def _db_schema():
    with flask_app.app_context():
        db.create_all()
        db.session.add(SystemConfig(
            id=1,
            minimumBookingTime=60,
            minimumCancellationTime=120,
            morningStartTime=dtime(7, 30),
            morningEndTime=dtime(11, 30),
            afternoonStartTime=dtime(13, 30),
            afternoonEndTime=dtime(17, 30),
            maxAppointmentsPerDay=1,
        ))
        db.session.commit()
    yield
    with flask_app.app_context():
        db.session.remove()
        db.engine.dispose()
    os.close(_fd)
    try:
        os.remove(_path)
    except OSError:
        pass


@pytest.fixture(autouse=True)
def app_context():
    ctx = flask_app.app_context()
    ctx.push()
    yield
    for table in reversed(db.metadata.sorted_tables):
        if table.name != "system_config":
            db.session.execute(table.delete())
    db.session.commit()
    ctx.pop()


@pytest.fixture
def client():
    return flask_app.test_client()


@pytest.fixture
def make_user():
    counter = {"n": 0}

    def _make(username, role=UserRoleEnum.PATIENT, password="Patient@123", name=None):
        counter["n"] += 1
        user = User(
            name=name or username,
            username=username,
            email=f"{username}{counter['n']}@test.local",
            password=password,
            role=role,
            gender=GenderEnum.MALE,
            phone="0900000000",
        )
        db.session.add(user)
        db.session.commit()
        return user
    return _make


@pytest.fixture
def specialization():
    spec = Specialization(name="Noi tong quat", icon="stethoscope")
    db.session.add(spec)
    db.session.commit()
    return spec


@pytest.fixture
def make_doctor(make_user, specialization):
    def _make(username="doc1", license_number="BS-001", fee=200000, experience_yrs=5, spec=None):
        user = make_user(username, role=UserRoleEnum.DOCTOR, password="Doctor@123")
        profile = DoctorProfile(
            user=user,
            specialization=spec or specialization,
            licenseNumber=license_number,
            experienceYrs=experience_yrs,
            fee=fee,
        )
        db.session.add(profile)
        db.session.commit()
        return user, profile
    return _make


@pytest.fixture
def login():
    def _login(client, username, password):
        return client.post("/login", data={"username": username, "password": password})
    return _login
