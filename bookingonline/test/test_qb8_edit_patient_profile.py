import pytest
from unittest.mock import MagicMock, patch
from datetime import date

from bookingonline import app
from bookingonline.models import dao


@pytest.fixture(autouse=True)
def app_context():
    with app.app_context():
        yield


@pytest.fixture
def mock_profile():
    profile = MagicMock()
    profile.id = 1
    profile.userId = 1
    profile.name = "Ten Cu"
    profile.phone = "0911111111"
    return profile


@patch("bookingonline.models.dao.PatientHealthProfile.query")
def test_get_patient_profile_by_owner_found(mock_query, mock_profile):
    mock_query.filter.return_value.first.return_value = mock_profile

    result = dao.get_patient_profile_by_owner(profile_id=1, user_id=1)

    assert result is mock_profile


@patch("bookingonline.models.dao.PatientHealthProfile.query")
def test_get_patient_profile_by_owner_wrong_owner_returns_none(mock_query):
    mock_query.filter.return_value.first.return_value = None

    result = dao.get_patient_profile_by_owner(profile_id=1, user_id=2)

    assert result is None


@patch("bookingonline.models.dao.PatientHealthProfile.query")
def test_get_patient_profile_by_owner_nonexistent_id_returns_none(mock_query):
    mock_query.filter.return_value.first.return_value = None

    result = dao.get_patient_profile_by_owner(profile_id=999999, user_id=1)

    assert result is None


@patch("bookingonline.models.dao.db.session")
def test_update_patient_profile_updates_fields(mock_session, mock_profile):
    dao.update_patient_profile(
        mock_profile,
        name="Ten Moi",
        phone="0922222222",
        address="Dia chi moi",
    )

    assert mock_profile.name == "Ten Moi"
    assert mock_profile.phone == "0922222222"
    assert mock_profile.address == "Dia chi moi"


@patch("bookingonline.models.dao.db.session")
def test_update_patient_profile_commits(mock_session, mock_profile):
    dao.update_patient_profile(mock_profile, name="Ten Moi", phone="0922222222")

    mock_session.commit.assert_called_once()


@patch("bookingonline.models.dao.db.session")
def test_update_patient_profile_does_not_touch_id_or_owner(mock_session, mock_profile):
    dao.update_patient_profile(mock_profile, name="Ten Moi", phone="0922222222")

    assert mock_profile.id == 1
    assert mock_profile.userId == 1
