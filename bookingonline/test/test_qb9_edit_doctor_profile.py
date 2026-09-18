import pytest
from unittest.mock import MagicMock, patch

from bookingonline import app
from bookingonline.models import dao


@pytest.fixture(autouse=True)
def app_context():
    with app.app_context():
        yield


@pytest.fixture
def mock_doctor_profile():
    profile = MagicMock()
    profile.userId = 1
    profile.licenseNumber = "BS-001"
    profile.experienceYrs = 5
    profile.fee = 200000
    profile.specializationId = 3
    profile.totalReview = 2
    profile.averageRating = 4.5
    return profile


@patch("bookingonline.models.dao.DoctorProfile.query")
def test_get_doctor_profile_by_user_filters_by_user_id(mock_query, mock_doctor_profile):
    mock_query.filter_by.return_value.first.return_value = mock_doctor_profile

    result = dao.get_doctor_profile_by_user(user_id=1)

    assert result is mock_doctor_profile
    mock_query.filter_by.assert_called_once_with(userId=1)


@patch("bookingonline.models.dao.DoctorProfile.query")
def test_get_doctor_profile_by_user_none_when_not_a_doctor(mock_query):
    mock_query.filter_by.return_value.first.return_value = None

    result = dao.get_doctor_profile_by_user(user_id=99)

    assert result is None


@patch("bookingonline.models.dao.db.session")
def test_update_doctor_profile_updates_whitelisted_fields(mock_session, mock_doctor_profile):
    dao.update_doctor_profile(
        mock_doctor_profile,
        license_number="BS-001-V2",
        experience_yrs=12,
        fee=275000,
        description="Mo ta moi",
        bio="Bio moi",
        avatar_url="https://example.com/a.jpg",
    )

    assert mock_doctor_profile.licenseNumber == "BS-001-V2"
    assert mock_doctor_profile.experienceYrs == 12
    assert mock_doctor_profile.fee == 275000
    assert mock_doctor_profile.description == "Mo ta moi"
    assert mock_doctor_profile.bio == "Bio moi"
    assert mock_doctor_profile.avatarUrl == "https://example.com/a.jpg"


@patch("bookingonline.models.dao.db.session")
def test_update_doctor_profile_commits(mock_session, mock_doctor_profile):
    dao.update_doctor_profile(mock_doctor_profile, license_number="BS-001", experience_yrs=5, fee=200000)

    mock_session.commit.assert_called_once()


@patch("bookingonline.models.dao.db.session")
def test_update_doctor_profile_does_not_touch_specialization_or_rating(mock_session, mock_doctor_profile):
    dao.update_doctor_profile(mock_doctor_profile, license_number="BS-001", experience_yrs=5, fee=200000)

    assert mock_doctor_profile.specializationId == 3
    assert mock_doctor_profile.totalReview == 2
    assert mock_doctor_profile.averageRating == 4.5
