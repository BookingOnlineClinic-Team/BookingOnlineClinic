import hashlib
import pytest
from unittest.mock import MagicMock, patch

from bookingonline import app
from bookingonline.models import dao


@pytest.fixture(autouse=True)
def app_context():
    with app.app_context():
        yield


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.username = "p1"
    user.password = "Patient@123"
    user.active = True
    return user


def test_hash_password_returns_md5_hex():
    result = dao.hash_password("Patient@123")

    assert result == hashlib.md5("Patient@123".encode("utf-8")).hexdigest()


def test_hash_password_is_deterministic():
    assert dao.hash_password("abc") == dao.hash_password("abc")


@patch("bookingonline.models.dao.User.query")
def test_verify_login_correct_credentials_returns_user(mock_query, mock_user):
    mock_query.filter_by.return_value.first.return_value = mock_user

    result = dao.verify_login("p1", "Patient@123")

    assert result is mock_user


@patch("bookingonline.models.dao.User.query")
def test_verify_login_wrong_password_returns_none(mock_query, mock_user):
    mock_query.filter_by.return_value.first.return_value = mock_user

    result = dao.verify_login("p1", "sai_mat_khau")

    assert result is None


@patch("bookingonline.models.dao.User.query")
def test_verify_login_inactive_user_returns_none(mock_query, mock_user):
    mock_user.active = False
    mock_query.filter_by.return_value.first.return_value = mock_user

    result = dao.verify_login("p1", "Patient@123")

    assert result is None


@patch("bookingonline.models.dao.User.query")
def test_verify_login_unknown_username_returns_none(mock_query):
    mock_query.filter_by.return_value.first.return_value = None

    result = dao.verify_login("khong_ton_tai", "x")

    assert result is None


@patch("bookingonline.models.dao.User.query")
def test_get_user_by_username_filters_by_role_when_given(mock_query, mock_user):
    mock_query.filter_by.return_value.filter_by.return_value.first.return_value = mock_user

    result = dao.get_user_by_username("p1", role="PATIENT")

    assert result is mock_user
    mock_query.filter_by.assert_called_once_with(username="p1")


@patch("bookingonline.models.dao.PatientHealthProfile.query")
def test_get_patient_profiles_by_owner_filters_by_user_id(mock_query):
    profile_1 = MagicMock()
    profile_2 = MagicMock()
    mock_query.filter_by.return_value.order_by.return_value.all.return_value = [profile_1, profile_2]

    result = dao.get_patient_profiles_by_owner(user_id=1)

    assert result == [profile_1, profile_2]
    mock_query.filter_by.assert_called_once_with(userId=1)


@patch("bookingonline.models.dao.PatientHealthProfile.query")
def test_get_patient_profiles_by_owner_empty_for_user_without_profile(mock_query):
    mock_query.filter_by.return_value.order_by.return_value.all.return_value = []

    result = dao.get_patient_profiles_by_owner(user_id=99)

    assert result == []
