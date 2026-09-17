import pytest
from unittest.mock import MagicMock, patch

from bookingonline import app
from bookingonline.models import dao


@pytest.fixture(autouse=True)
def app_context():
    with app.app_context():
        yield


@pytest.fixture
def mock_doctor():
    # Giả lập 1 DoctorProfile, có sẵn user gắn kèm (giống quan hệ thật doctor.user)
    doctor = MagicMock()
    doctor.user = MagicMock()
    doctor.user.active = True
    return doctor


# ---- Sửa thông tin bác sĩ ----

@patch("bookingonline.models.dao.db.session")
def test_update_doctor_updates_user_fields(mock_session, mock_doctor):
    # Sửa xong thì các field trên user phải đúng giá trị mới
    dao.update_doctor_account(
        mock_doctor, name="Ten Moi", email="moi@example.com",
        specialization_id=2, license_number="GP-002",
        experience_yrs=7, fee=250000,
    )

    assert mock_doctor.user.name == "Ten Moi"
    assert mock_doctor.user.email == "moi@example.com"


@patch("bookingonline.models.dao.db.session")
def test_update_doctor_updates_profile_fields(mock_session, mock_doctor):
    # Sửa xong thì các field trên profile (chuyên khoa, kinh nghiệm, phí...) phải đúng
    dao.update_doctor_account(
        mock_doctor, name="A", email="a@example.com",
        specialization_id=2, license_number="GP-002",
        experience_yrs=7, fee=250000,
    )

    assert mock_doctor.specializationId == 2
    assert mock_doctor.licenseNumber == "GP-002"
    assert mock_doctor.experienceYrs == 7
    assert mock_doctor.fee == 250000
    mock_session.commit.assert_called_once()


@patch("bookingonline.models.dao.db.session")
def test_update_doctor_not_change_username_password(mock_session, mock_doctor):
    # QUAN TRỌNG: sửa hồ sơ không được đụng vào username/password
    mock_doctor.user.username = "username_cu"
    mock_doctor.user.password = "password_cu"

    dao.update_doctor_account(
        mock_doctor, name="A", email="a@example.com",
        specialization_id=1, license_number="GP-001",
        experience_yrs=1, fee=100000,
    )

    assert mock_doctor.user.username == "username_cu"
    assert mock_doctor.user.password == "password_cu"


# ---- Khóa / Mở khóa tài khoản ----

@patch("bookingonline.models.dao.db.session")
def test_toggle_active_lock(mock_session, mock_doctor):
    # Đang active=True -> gọi 1 lần thành False (khóa lại)
    mock_doctor.user.active = True

    dao.toggle_doctor_active(mock_doctor)

    assert mock_doctor.user.active is False
    mock_session.commit.assert_called_once()


@patch("bookingonline.models.dao.db.session")
def test_toggle_active_unlock(mock_session, mock_doctor):
    # Đang active=False -> gọi 1 lần thành True (mở khóa)
    mock_doctor.user.active = False

    dao.toggle_doctor_active(mock_doctor)

    assert mock_doctor.user.active is True


# ---- Đặt lại mật khẩu ----

@patch("bookingonline.models.dao.db.session")
def test_reset_password_updates_user_password(mock_session, mock_doctor):
    dao.reset_doctor_password(mock_doctor, "matkhaumoi123")

    assert mock_doctor.user.password == "matkhaumoi123"
    mock_session.commit.assert_called_once()