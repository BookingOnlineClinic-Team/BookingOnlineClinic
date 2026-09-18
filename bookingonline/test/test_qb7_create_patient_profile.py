import pytest
from unittest.mock import MagicMock, patch
from datetime import date

from bookingonline import app
from bookingonline.models import dao
from bookingonline.models.models import GenderEnum


@pytest.fixture(autouse=True)
def app_context():
    with app.app_context():
        yield


@pytest.fixture
def mock_owner():
    owner = MagicMock()
    owner.id = 1
    return owner


@patch("bookingonline.models.dao.db.session")
def test_create_patient_profile_sets_fields_from_args(mock_session, mock_owner):
    profile = dao.create_patient_profile(
        owner=mock_owner,
        name="Nguyen Van A",
        phone="0911111111",
        gender=GenderEnum.MALE,
        date_of_birth=date(1990, 5, 20),
        address="12 Nguyen Trai",
    )

    assert profile.owner is mock_owner
    assert profile.name == "Nguyen Van A"
    assert profile.phone == "0911111111"
    assert profile.gender == GenderEnum.MALE
    assert profile.dateOfBirth == date(1990, 5, 20)
    assert profile.address == "12 Nguyen Trai"


@patch("bookingonline.models.dao.db.session")
def test_create_patient_profile_adds_and_commits(mock_session, mock_owner):
    profile = dao.create_patient_profile(owner=mock_owner, name="Nguyen Van A", phone="0911111111")

    mock_session.add.assert_called_once_with(profile)
    mock_session.commit.assert_called_once()


@patch("bookingonline.models.dao.db.session")
def test_create_patient_profile_optional_fields_default_none(mock_session, mock_owner):
    profile = dao.create_patient_profile(owner=mock_owner, name="Nguyen Van A", phone="0911111111")

    assert profile.gender is None
    assert profile.dateOfBirth is None
    assert profile.address is None


@patch("bookingonline.models.dao.PatientHealthProfile.query")
def test_search_patient_profile_found(mock_query):
    mock_profile = MagicMock()
    mock_query.filter_by.return_value.first.return_value = mock_profile

    result = dao.search_patient_profile(phone="0911111111", name="Nguyen Van A")

    assert result is mock_profile
    mock_query.filter_by.assert_called_once_with(phone="0911111111", name="Nguyen Van A")


@patch("bookingonline.models.dao.PatientHealthProfile.query")
def test_search_patient_profile_not_found_returns_none(mock_query):
    mock_query.filter_by.return_value.first.return_value = None

    result = dao.search_patient_profile(phone="0900000000", name="Khong Ton Tai")

    assert result is None
