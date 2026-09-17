import pytest
from datetime import date, time, timedelta
from unittest.mock import MagicMock, patch

from bookingonline import app, db
from bookingonline.models import dao
from bookingonline.models.models import (
    WorkSchedule,
    WorkScheduleSessionEnum,
)


# ============================================================
# FLASK APPLICATION CONTEXT
# ============================================================

@pytest.fixture(autouse=True)
def app_context():
    app.config["TESTING"] = True

    with app.app_context():
        yield


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def mock_config():
    """
    Dùng đúng cấu hình hiện tại của project.
    Không thay đổi fallback trong dao.py.
    """
    config = MagicMock()

    config.morningStartTime = time(7, 30)
    config.morningEndTime = time(11, 30)

    config.afternoonStartTime = time(13, 30)
    config.afternoonEndTime = time(17, 30)

    return config


@pytest.fixture
def work_date():
    return date(2026, 9, 21)


# ============================================================
# QB-26 - CHỈ ĐƯỢC CẤU HÌNH TUẦN KẾ TIẾP
# ============================================================

def test_qb26_can_configure_next_week():
    """
    QB-26:
    Tuần kế tiếp phải được phép cấu hình.
    """

    today = date.today()

    current_week = (
        today - timedelta(days=today.weekday())
    )

    next_week = current_week + timedelta(days=7)

    result = dao.can_configure_schedule_week(
        next_week
    )

    assert result is True


def test_qb26_cannot_configure_current_week():
    """
    QB-26:
    Không được cấu hình tuần hiện tại.
    """

    today = date.today()

    current_week = (
        today - timedelta(days=today.weekday())
    )

    result = dao.can_configure_schedule_week(
        current_week
    )

    assert result is False


@pytest.mark.parametrize(
    "offset",
    [
        -7,     # tuần trước
        14,     # sau 2 tuần
        21,     # sau 3 tuần
    ]
)
def test_qb26_cannot_configure_other_weeks(
    offset
):
    """
    QB-26:
    Ngoài tuần kế tiếp đều không được cấu hình.
    """

    today = date.today()

    current_week = (
        today - timedelta(days=today.weekday())
    )

    target_week = (
        current_week + timedelta(days=offset)
    )

    result = dao.can_configure_schedule_week(
        target_week
    )

    assert result is False


# ============================================================
# QB-26 - THÊM CA SÁNG MỚI
# ============================================================

@patch("bookingonline.models.dao.db.session.add")
@patch(
    "bookingonline.models.dao."
    "get_work_schedule_by_doctor_date_session"
)
@patch("bookingonline.models.dao.get_system_config")
def test_qb26_create_new_morning_schedule(
    mock_get_config,
    mock_get_schedule,
    mock_add,
    mock_config,
    work_date
):
    """
    QB-26:
    Doctor chọn ca sáng chưa tồn tại
    -> tạo WorkSchedule mới.
    """

    mock_get_config.return_value = mock_config
    mock_get_schedule.return_value = None

    dao.save_doctor_work_schedule(
        doctor_id=1,
        work_date=work_date,
        session=WorkScheduleSessionEnum.MORNING,
        is_selected=True
    )

    mock_add.assert_called_once()

    new_schedule = mock_add.call_args.args[0]

    assert isinstance(
        new_schedule,
        WorkSchedule
    )

    assert new_schedule.doctorId == 1
    assert new_schedule.workDate == work_date

    assert (
        new_schedule.session
        == WorkScheduleSessionEnum.MORNING
    )

    assert (
        new_schedule.startTime
        == mock_config.morningStartTime
    )

    assert (
        new_schedule.endTime
        == mock_config.morningEndTime
    )

    assert new_schedule.isAvailable is True


# ============================================================
# QB-26 - THÊM CA CHIỀU MỚI
# ============================================================

@patch("bookingonline.models.dao.db.session.add")
@patch(
    "bookingonline.models.dao."
    "get_work_schedule_by_doctor_date_session"
)
@patch("bookingonline.models.dao.get_system_config")
def test_qb26_create_new_afternoon_schedule(
    mock_get_config,
    mock_get_schedule,
    mock_add,
    mock_config,
    work_date
):
    """
    QB-26:
    Doctor chọn ca chiều chưa tồn tại
    -> tạo WorkSchedule với đúng giờ chiều.
    """

    mock_get_config.return_value = mock_config
    mock_get_schedule.return_value = None

    dao.save_doctor_work_schedule(
        doctor_id=1,
        work_date=work_date,
        session=WorkScheduleSessionEnum.AFTERNOON,
        is_selected=True
    )

    mock_add.assert_called_once()

    new_schedule = mock_add.call_args.args[0]

    assert (
        new_schedule.session
        == WorkScheduleSessionEnum.AFTERNOON
    )

    assert (
        new_schedule.startTime
        == mock_config.afternoonStartTime
    )

    assert (
        new_schedule.endTime
        == mock_config.afternoonEndTime
    )

    assert new_schedule.isAvailable is True


# ============================================================
# QB-26 - BẬT LẠI CA ĐÃ TỒN TẠI
# ============================================================

@patch(
    "bookingonline.models.dao."
    "get_work_schedule_by_doctor_date_session"
)
@patch("bookingonline.models.dao.get_system_config")
def test_qb26_enable_existing_schedule(
    mock_get_config,
    mock_get_schedule,
    mock_config,
    work_date
):
    """
    QB-26:
    Ca đã tồn tại nhưng đang unavailable.
    Khi doctor chọn lại -> bật isAvailable.
    """

    existing = MagicMock(
        spec=WorkSchedule
    )

    existing.isAvailable = False

    mock_get_config.return_value = mock_config
    mock_get_schedule.return_value = existing

    dao.save_doctor_work_schedule(
        doctor_id=1,
        work_date=work_date,
        session=WorkScheduleSessionEnum.MORNING,
        is_selected=True
    )

    assert existing.isAvailable is True

    assert (
        existing.startTime
        == mock_config.morningStartTime
    )

    assert (
        existing.endTime
        == mock_config.morningEndTime
    )


# ============================================================
# QB-26 - BỎ CA KHÔNG CÓ APPOINTMENT CONFIRMED
# ============================================================

@patch(
    "bookingonline.models.dao."
    "has_confirmed_appointment_in_schedule"
)
@patch(
    "bookingonline.models.dao."
    "get_work_schedule_by_doctor_date_session"
)
@patch("bookingonline.models.dao.get_system_config")
def test_qb26_disable_schedule_without_confirmed_appointment(
    mock_get_config,
    mock_get_schedule,
    mock_has_confirmed,
    mock_config,
    work_date
):
    """
    QB-26:
    Ca tồn tại nhưng không có lịch hẹn CONFIRMED
    -> bác sĩ được phép bỏ ca.
    """

    existing = MagicMock(
        spec=WorkSchedule
    )

    existing.isAvailable = True

    mock_get_config.return_value = mock_config
    mock_get_schedule.return_value = existing

    mock_has_confirmed.return_value = False

    dao.save_doctor_work_schedule(
        doctor_id=1,
        work_date=work_date,
        session=WorkScheduleSessionEnum.MORNING,
        is_selected=False
    )

    assert existing.isAvailable is False

    mock_has_confirmed.assert_called_once()


# ============================================================
# QB-26 - KHÔNG ĐƯỢC BỎ CA ĐÃ CÓ CONFIRMED APPOINTMENT
# ============================================================

@patch(
    "bookingonline.models.dao."
    "has_confirmed_appointment_in_schedule"
)
@patch(
    "bookingonline.models.dao."
    "get_work_schedule_by_doctor_date_session"
)
@patch("bookingonline.models.dao.get_system_config")
def test_qb26_cannot_disable_confirmed_schedule(
    mock_get_config,
    mock_get_schedule,
    mock_has_confirmed,
    mock_config,
    work_date
):
    """
    QB-26:
    Nếu ca đã có appointment CONFIRMED
    -> phải raise ValueError.
    """

    existing = MagicMock(
        spec=WorkSchedule
    )

    existing.isAvailable = True

    mock_get_config.return_value = mock_config
    mock_get_schedule.return_value = existing

    mock_has_confirmed.return_value = True

    with pytest.raises(
        ValueError,
        match="Không thể bỏ ca làm việc"
    ):
        dao.save_doctor_work_schedule(
            doctor_id=1,
            work_date=work_date,
            session=WorkScheduleSessionEnum.MORNING,
            is_selected=False
        )

    # Không được tắt ca
    assert existing.isAvailable is True


# ============================================================
# QB-26 - UPDATE CẢ TUẦN
# ============================================================

@patch("bookingonline.models.dao.db.session.commit")
@patch(
    "bookingonline.models.dao."
    "save_doctor_work_schedule"
)
@patch(
    "bookingonline.models.dao."
    "is_clinic_working_day"
)
def test_qb26_update_week_schedule(
    mock_working_day,
    mock_save_schedule,
    mock_commit
):
    """
    QB-26:
    Update lịch tuần:
    - duyệt 7 ngày
    - mỗi ngày xử lý MORNING + AFTERNOON
    - commit sau khi hoàn tất.
    """

    week_start = date(2026, 9, 21)

    mock_working_day.return_value = True

    selected_sessions = set()

    dao.update_doctor_week_schedule(
        doctor_id=1,
        week_start=week_start,
        selected_sessions=selected_sessions
    )

    # 7 ngày x 2 ca
    assert mock_save_schedule.call_count == 14

    assert mock_working_day.call_count == 7

    mock_commit.assert_called_once()


# ============================================================
# QB-26 - BỎ QUA NGÀY PHÒNG KHÁM KHÔNG LÀM
# ============================================================

@patch("bookingonline.models.dao.db.session.commit")
@patch(
    "bookingonline.models.dao."
    "save_doctor_work_schedule"
)
@patch(
    "bookingonline.models.dao."
    "is_clinic_working_day"
)
def test_qb26_skip_clinic_non_working_day(
    mock_working_day,
    mock_save_schedule,
    mock_commit
):
    """
    QB-26:
    Nếu bệnh viện không làm việc ngày đó
    -> không tạo/cập nhật ca cho ngày đó.
    """

    week_start = date(2026, 9, 21)

    # Ngày đầu nghỉ, 6 ngày còn lại làm
    mock_working_day.side_effect = [
        False,
        True,
        True,
        True,
        True,
        True,
        True,
    ]

    dao.update_doctor_week_schedule(
        doctor_id=1,
        week_start=week_start,
        selected_sessions=set()
    )

    # 6 ngày làm x 2 ca
    assert mock_save_schedule.call_count == 12

    assert mock_working_day.call_count == 7

    mock_commit.assert_called_once()


# ============================================================
# QB-26 - CA ĐƯỢC CHỌN PHẢI TRUYỀN is_selected=True
# ============================================================

@patch("bookingonline.models.dao.db.session.commit")
@patch(
    "bookingonline.models.dao."
    "save_doctor_work_schedule"
)
@patch(
    "bookingonline.models.dao."
    "is_clinic_working_day"
)
def test_qb26_selected_session_is_saved_as_true(
    mock_working_day,
    mock_save_schedule,
    mock_commit
):
    """
    QB-26:
    Session được doctor tick chọn
    phải được truyền is_selected=True.
    """

    week_start = date(2026, 9, 21)

    mock_working_day.return_value = True

    selected_sessions = {
        "2026-09-21_MORNING"
    }

    dao.update_doctor_week_schedule(
        doctor_id=1,
        week_start=week_start,
        selected_sessions=selected_sessions
    )

    first_call = (
        mock_save_schedule.call_args_list[0]
    )

    assert first_call.kwargs[
        "doctor_id"
    ] == 1

    assert first_call.kwargs[
        "work_date"
    ] == date(2026, 9, 21)

    assert first_call.kwargs[
        "session"
    ] == WorkScheduleSessionEnum.MORNING

    assert first_call.kwargs[
        "is_selected"
    ] is True

    mock_commit.assert_called_once()