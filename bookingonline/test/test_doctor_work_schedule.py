import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

from bookingonline import app
from bookingonline.index import doctor_work_schedule
from bookingonline.models.models import UserRoleEnum


# ============================================================
# FLASK APPLICATION CONTEXT
# ============================================================

@pytest.fixture(autouse=True)
def app_context():
    app.config["TESTING"] = True

    with app.app_context():
        yield


@pytest.fixture
def mock_doctor():
    doctor = MagicMock()
    doctor.id = 10
    return doctor


# ============================================================
# QB-25 - USER KHÔNG PHẢI DOCTOR
# ============================================================

@pytest.mark.parametrize(
    "role",
    [
        UserRoleEnum.PATIENT,
        UserRoleEnum.ADMIN,
    ]
)
@patch("bookingonline.index.url_for")
@patch("bookingonline.index.flash")
@patch("bookingonline.index.current_user")
def test_qb25_non_doctor_cannot_view_schedule(
    mock_current_user,
    mock_flash,
    mock_url_for,
    role
):
    """
    QB-25:
    Chỉ bác sĩ mới được xem lịch làm việc của mình.
    """

    mock_current_user.role = role

    mock_url_for.return_value = "/"

    with app.test_request_context(
        "/doctor/work-schedule"
    ):
        response = doctor_work_schedule.__wrapped__()

    assert response.status_code == 302
    assert response.location == "/"

    mock_flash.assert_called_once()
    mock_url_for.assert_called()


# ============================================================
# QB-25 - KHÔNG CÓ DOCTOR PROFILE
# ============================================================

@patch("bookingonline.index.url_for")
@patch("bookingonline.index.flash")
@patch(
    "bookingonline.index.dao.get_doctor_profile_by_user"
)
@patch("bookingonline.index.current_user")
def test_qb25_doctor_profile_not_found(
    mock_current_user,
    mock_get_doctor,
    mock_flash,
    mock_url_for
):
    """
    QB-25:
    User là DOCTOR nhưng không có DoctorProfile
    -> không thể xem lịch.
    """

    mock_current_user.role = UserRoleEnum.DOCTOR
    mock_current_user.id = 100

    mock_get_doctor.return_value = None
    mock_url_for.return_value = "/"

    with app.test_request_context(
        "/doctor/work-schedule"
    ):
        response = doctor_work_schedule.__wrapped__()

    assert response.status_code == 302
    assert response.location == "/"

    mock_get_doctor.assert_called_once_with(100)
    mock_flash.assert_called_once()


# ============================================================
# QB-25 - XEM TUẦN HIỆN TẠI
# ============================================================

@patch("bookingonline.index.render_template")
@patch("bookingonline.index.dao.get_system_config")
@patch(
    "bookingonline.index.dao.build_doctor_week_schedule"
)
@patch(
    "bookingonline.index.dao.get_doctor_profile_by_user"
)
@patch("bookingonline.index.current_user")
def test_qb25_view_current_week_success(
    mock_current_user,
    mock_get_doctor,
    mock_build_schedule,
    mock_get_config,
    mock_render_template,
    mock_doctor
):
    """
    QB-25:
    Bác sĩ xem lịch tuần hiện tại thành công.
    """

    mock_current_user.role = UserRoleEnum.DOCTOR
    mock_current_user.id = 100

    mock_get_doctor.return_value = mock_doctor
    mock_build_schedule.return_value = []
    mock_get_config.return_value = MagicMock()

    mock_render_template.return_value = "OK"

    with app.test_request_context(
        "/doctor/work-schedule"
    ):
        response = doctor_work_schedule.__wrapped__()

    assert response == "OK"

    today = date.today()

    expected_week = (
        today
        - timedelta(days=today.weekday())
    )

    mock_get_doctor.assert_called_once_with(100)

    mock_build_schedule.assert_called_once_with(
        mock_doctor.id,
        expected_week
    )


# ============================================================
# QB-25 - XEM TUẦN QUÁ KHỨ
# ============================================================

@patch("bookingonline.index.render_template")
@patch("bookingonline.index.dao.get_system_config")
@patch(
    "bookingonline.index.dao.build_doctor_week_schedule"
)
@patch(
    "bookingonline.index.dao.get_doctor_profile_by_user"
)
@patch("bookingonline.index.current_user")
def test_qb25_can_view_previous_week(
    mock_current_user,
    mock_get_doctor,
    mock_build_schedule,
    mock_get_config,
    mock_render_template,
    mock_doctor
):
    """
    QB-25:
    Bác sĩ được phép xem lịch tuần quá khứ.
    """

    mock_current_user.role = UserRoleEnum.DOCTOR
    mock_current_user.id = 100

    mock_get_doctor.return_value = mock_doctor
    mock_build_schedule.return_value = []
    mock_get_config.return_value = MagicMock()

    mock_render_template.return_value = "OK"

    previous_week = date(2026, 9, 7)

    with app.test_request_context(
        "/doctor/work-schedule"
        "?week=2026-09-07"
    ):
        response = doctor_work_schedule.__wrapped__()

    assert response == "OK"

    mock_build_schedule.assert_called_once_with(
        mock_doctor.id,
        previous_week
    )


# ============================================================
# QB-25 - XEM TUẦN KẾ TIẾP
# ============================================================

@patch("bookingonline.index.render_template")
@patch("bookingonline.index.dao.get_system_config")
@patch(
    "bookingonline.index.dao.build_doctor_week_schedule"
)
@patch(
    "bookingonline.index.dao.get_doctor_profile_by_user"
)
@patch("bookingonline.index.current_user")
def test_qb25_can_view_next_week(
    mock_current_user,
    mock_get_doctor,
    mock_build_schedule,
    mock_get_config,
    mock_render_template,
    mock_doctor
):
    """
    QB-25:
    Bác sĩ được phép xem tuần kế tiếp.
    """

    mock_current_user.role = UserRoleEnum.DOCTOR
    mock_current_user.id = 100

    mock_get_doctor.return_value = mock_doctor
    mock_build_schedule.return_value = []
    mock_get_config.return_value = MagicMock()

    mock_render_template.return_value = "OK"

    today = date.today()

    current_week = (
        today
        - timedelta(days=today.weekday())
    )

    next_week = (
        current_week
        + timedelta(days=7)
    )

    url = (
        "/doctor/work-schedule"
        f"?week={next_week.isoformat()}"
    )

    with app.test_request_context(url):
        response = doctor_work_schedule.__wrapped__()

    assert response == "OK"

    mock_build_schedule.assert_called_once_with(
        mock_doctor.id,
        next_week
    )


# ============================================================
# QB-25 - GIỚI HẠN TỐI ĐA TUẦN KẾ TIẾP
# ============================================================

@patch("bookingonline.index.render_template")
@patch("bookingonline.index.dao.get_system_config")
@patch(
    "bookingonline.index.dao.build_doctor_week_schedule"
)
@patch(
    "bookingonline.index.dao.get_doctor_profile_by_user"
)
@patch("bookingonline.index.current_user")
def test_qb25_future_week_is_limited(
    mock_current_user,
    mock_get_doctor,
    mock_build_schedule,
    mock_get_config,
    mock_render_template,
    mock_doctor
):
    """
    QB-25:
    Nếu yêu cầu tuần xa hơn tuần kế tiếp,
    hệ thống clamp về tuần kế tiếp.
    """

    mock_current_user.role = UserRoleEnum.DOCTOR
    mock_current_user.id = 100

    mock_get_doctor.return_value = mock_doctor
    mock_build_schedule.return_value = []
    mock_get_config.return_value = MagicMock()

    mock_render_template.return_value = "OK"

    today = date.today()

    current_week = (
        today
        - timedelta(days=today.weekday())
    )

    max_week = (
        current_week
        + timedelta(days=7)
    )

    far_future = (
        current_week
        + timedelta(days=35)
    )

    url = (
        "/doctor/work-schedule"
        f"?week={far_future.isoformat()}"
    )

    with app.test_request_context(url):
        response = doctor_work_schedule.__wrapped__()

    assert response == "OK"

    mock_build_schedule.assert_called_once_with(
        mock_doctor.id,
        max_week
    )


# ============================================================
# QB-25 - WEEK SAI ĐỊNH DẠNG
# ============================================================

@patch("bookingonline.index.render_template")
@patch("bookingonline.index.dao.get_system_config")
@patch(
    "bookingonline.index.dao.build_doctor_week_schedule"
)
@patch(
    "bookingonline.index.dao.get_doctor_profile_by_user"
)
@patch("bookingonline.index.current_user")
def test_qb25_invalid_week_uses_current_week(
    mock_current_user,
    mock_get_doctor,
    mock_build_schedule,
    mock_get_config,
    mock_render_template,
    mock_doctor
):
    """
    QB-25:
    week sai định dạng
    -> sử dụng tuần hiện tại.
    """

    mock_current_user.role = UserRoleEnum.DOCTOR
    mock_current_user.id = 100

    mock_get_doctor.return_value = mock_doctor
    mock_build_schedule.return_value = []
    mock_get_config.return_value = MagicMock()

    mock_render_template.return_value = "OK"

    with app.test_request_context(
        "/doctor/work-schedule?week=abc"
    ):
        response = doctor_work_schedule.__wrapped__()

    assert response == "OK"

    today = date.today()

    current_week = (
        today
        - timedelta(days=today.weekday())
    )

    mock_build_schedule.assert_called_once_with(
        mock_doctor.id,
        current_week
    )


# ============================================================
# QB-25 - TRUYỀN NGÀY GIỮA TUẦN
# ============================================================

@patch("bookingonline.index.render_template")
@patch("bookingonline.index.dao.get_system_config")
@patch(
    "bookingonline.index.dao.build_doctor_week_schedule"
)
@patch(
    "bookingonline.index.dao.get_doctor_profile_by_user"
)
@patch("bookingonline.index.current_user")
def test_qb25_middle_of_week_normalized_to_monday(
    mock_current_user,
    mock_get_doctor,
    mock_build_schedule,
    mock_get_config,
    mock_render_template,
    mock_doctor
):
    """
    QB-25:
    Nếu week là một ngày giữa tuần,
    phải quy về thứ Hai của tuần đó.
    """

    mock_current_user.role = UserRoleEnum.DOCTOR
    mock_current_user.id = 100

    mock_get_doctor.return_value = mock_doctor
    mock_build_schedule.return_value = []
    mock_get_config.return_value = MagicMock()

    mock_render_template.return_value = "OK"

    with app.test_request_context(
        "/doctor/work-schedule"
        "?week=2026-09-16"
    ):
        response = doctor_work_schedule.__wrapped__()

    assert response == "OK"

    mock_build_schedule.assert_called_once_with(
        mock_doctor.id,
        date(2026, 9, 14)
    )