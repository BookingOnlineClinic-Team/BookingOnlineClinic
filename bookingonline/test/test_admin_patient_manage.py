import pytest
from unittest.mock import MagicMock, patch

from bookingonline import app
from bookingonline.models import dao


@pytest.fixture(autouse=True)
def app_context():
    with app.app_context():
        yield


@pytest.fixture
def mock_patient_user():
    # Giả lập 1 User role PATIENT
    user = MagicMock()
    user.active = True
    return user


# ---- Đếm hồ sơ sức khỏe của bệnh nhân ----

@patch("bookingonline.models.dao.PatientHealthProfile.query")
def test_count_health_profiles(mock_query):
    mock_query.filter_by.return_value.count.return_value = 2

    result = dao.count_health_profiles_for_patient(user_id=1)

    assert result == 2
    mock_query.filter_by.assert_called_once_with(userId=1)


# ---- Đếm lịch hẹn của bệnh nhân ----

@patch("bookingonline.models.dao.Appointment.query")
def test_count_appointments(mock_query):
    joined_query = mock_query.join.return_value
    joined_query.filter.return_value.count.return_value = 5

    result = dao.count_appointments_for_patient(user_id=1)

    assert result == 5


# ---- Khóa / Mở khóa tài khoản ----

@patch("bookingonline.models.dao.db.session")
def test_toggle_user_active_lock(mock_session, mock_patient_user):
    # Đang active=True -> gọi xong thành False
    mock_patient_user.active = True

    dao.toggle_user_active(mock_patient_user)

    assert mock_patient_user.active is False
    mock_session.commit.assert_called_once()


@patch("bookingonline.models.dao.db.session")
def test_toggle_user_active_unlock(mock_session, mock_patient_user):
    # Đang active=False -> gọi xong thành True
    mock_patient_user.active = False

    dao.toggle_user_active(mock_patient_user)

    assert mock_patient_user.active is True