import pytest
from datetime import date, time, timedelta
from unittest.mock import MagicMock, patch

from bookingonline import app
from bookingonline.models import dao
from bookingonline.models.models import (
    WorkSchedule,
    Appointment,
    WorkScheduleSessionEnum,
)


# ============================================================
# FLASK APPLICATION CONTEXT
# ============================================================

@pytest.fixture(autouse=True)
def app_context():
    with app.app_context():
        yield


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def week_start():
    # Thứ Hai
    return date(2026, 9, 14)


@pytest.fixture
def mock_config():
    config = MagicMock()
    config.afternoonStartTime = time(13, 30)
    return config


# ============================================================
# QB-24 - XÁC ĐỊNH ĐẦU TUẦN
# ============================================================

@pytest.mark.parametrize(
    "target_date, expected_monday",
    [
        (
            date(2026, 9, 14),
            date(2026, 9, 14)
        ),
        (
            date(2026, 9, 16),
            date(2026, 9, 14)
        ),
        (
            date(2026, 9, 20),
            date(2026, 9, 14)
        ),
    ]
)
def test_qb24_get_week_start(
    target_date,
    expected_monday
):
    """
    QB-24:
    Lịch được xem theo tuần.

    Dù truyền thứ Hai, giữa tuần hay Chủ Nhật
    thì phải xác định đúng ngày đầu tuần là thứ Hai.
    """

    result = dao.get_week_start(target_date)

    assert result == expected_monday


# ============================================================
# QB-24 - LẤY LỊCH TRONG ĐÚNG 1 TUẦN
# ============================================================

@patch("bookingonline.models.dao.WorkSchedule.query")
def test_qb24_get_work_schedules_by_week(
    mock_query,
    week_start
):
    """
    QB-24:
    Query lịch làm việc phải giới hạn
    từ thứ Hai đến Chủ Nhật.
    """

    filtered_query = mock_query.filter.return_value
    ordered_query = filtered_query.order_by.return_value

    ordered_query.all.return_value = []

    result = dao.get_doctor_work_schedules_by_week(
        doctor_id=1,
        week_start=week_start
    )

    assert result == []

    mock_query.filter.assert_called_once()

    conditions = mock_query.filter.call_args.args

    assert len(conditions) == 3

    week_end = week_start + timedelta(days=6)

    assert str(
        conditions[0]
    ) == str(
        WorkSchedule.doctorId == 1
    )

    assert str(
        conditions[1]
    ) == str(
        WorkSchedule.workDate >= week_start
    )

    assert str(
        conditions[2]
    ) == str(
        WorkSchedule.workDate <= week_end
    )


# ============================================================
# QB-24 - BUILD ĐÚNG 7 NGÀY
# ============================================================

@patch("bookingonline.models.dao.get_system_config")
@patch("bookingonline.models.dao.get_doctor_appointments_by_week")
@patch("bookingonline.models.dao.get_doctor_work_schedules_by_week")
def test_qb24_build_schedule_has_7_days(
    mock_get_schedules,
    mock_get_appointments,
    mock_get_config,
    week_start,
    mock_config
):
    """
    QB-24:
    Lịch tuần phải luôn có đúng 7 ngày.
    """

    mock_get_schedules.return_value = []
    mock_get_appointments.return_value = []
    mock_get_config.return_value = mock_config

    result = dao.build_doctor_week_schedule(
        doctor_id=1,
        week_start=week_start
    )

    assert len(result) == 7

    assert result[0]["date"] == week_start

    assert result[6]["date"] == (
        week_start + timedelta(days=6)
    )


# ============================================================
# QB-24 - NGÀY KHÔNG CÓ LỊCH
# ============================================================

@patch("bookingonline.models.dao.get_system_config")
@patch("bookingonline.models.dao.get_doctor_appointments_by_week")
@patch("bookingonline.models.dao.get_doctor_work_schedules_by_week")
def test_qb24_day_without_schedule(
    mock_get_schedules,
    mock_get_appointments,
    mock_get_config,
    week_start,
    mock_config
):
    """
    QB-24:
    Ngày không có lịch làm việc
    -> morning và afternoon đều None.
    """

    mock_get_schedules.return_value = []
    mock_get_appointments.return_value = []
    mock_get_config.return_value = mock_config

    result = dao.build_doctor_week_schedule(
        doctor_id=1,
        week_start=week_start
    )

    first_day = result[0]

    assert first_day["morning"] is None
    assert first_day["afternoon"] is None

    assert first_day["morning_appointments"] == []
    assert first_day["afternoon_appointments"] == []


# ============================================================
# QB-24 - HIỂN THỊ CA SÁNG
# ============================================================

@patch("bookingonline.models.dao.get_system_config")
@patch("bookingonline.models.dao.get_doctor_appointments_by_week")
@patch("bookingonline.models.dao.get_doctor_work_schedules_by_week")
def test_qb24_show_morning_schedule(
    mock_get_schedules,
    mock_get_appointments,
    mock_get_config,
    week_start,
    mock_config
):
    """
    QB-24:
    Ca MORNING phải được gắn đúng vào
    trường morning của ngày tương ứng.
    """

    morning_schedule = MagicMock(
        spec=WorkSchedule
    )

    morning_schedule.workDate = week_start
    morning_schedule.session = (
        WorkScheduleSessionEnum.MORNING
    )

    mock_get_schedules.return_value = [
        morning_schedule
    ]

    mock_get_appointments.return_value = []
    mock_get_config.return_value = mock_config

    result = dao.build_doctor_week_schedule(
        doctor_id=1,
        week_start=week_start
    )

    first_day = result[0]

    assert first_day["morning"] == morning_schedule
    assert first_day["afternoon"] is None


# ============================================================
# QB-24 - HIỂN THỊ CA CHIỀU
# ============================================================

@patch("bookingonline.models.dao.get_system_config")
@patch("bookingonline.models.dao.get_doctor_appointments_by_week")
@patch("bookingonline.models.dao.get_doctor_work_schedules_by_week")
def test_qb24_show_afternoon_schedule(
    mock_get_schedules,
    mock_get_appointments,
    mock_get_config,
    week_start,
    mock_config
):
    """
    QB-24:
    Ca AFTERNOON phải được gắn đúng vào
    trường afternoon của ngày tương ứng.
    """

    afternoon_schedule = MagicMock(
        spec=WorkSchedule
    )

    afternoon_schedule.workDate = week_start
    afternoon_schedule.session = (
        WorkScheduleSessionEnum.AFTERNOON
    )

    mock_get_schedules.return_value = [
        afternoon_schedule
    ]

    mock_get_appointments.return_value = []
    mock_get_config.return_value = mock_config

    result = dao.build_doctor_week_schedule(
        doctor_id=1,
        week_start=week_start
    )

    first_day = result[0]

    assert first_day["morning"] is None
    assert first_day["afternoon"] == afternoon_schedule


# ============================================================
# QB-24 - HIỂN THỊ CẢ 2 CA
# ============================================================

@patch("bookingonline.models.dao.get_system_config")
@patch("bookingonline.models.dao.get_doctor_appointments_by_week")
@patch("bookingonline.models.dao.get_doctor_work_schedules_by_week")
def test_qb24_show_both_sessions(
    mock_get_schedules,
    mock_get_appointments,
    mock_get_config,
    week_start,
    mock_config
):
    """
    QB-24:
    Một ngày có cả ca sáng và ca chiều
    -> phải hiển thị đúng cả hai.
    """

    morning_schedule = MagicMock(
        spec=WorkSchedule
    )
    morning_schedule.workDate = week_start
    morning_schedule.session = (
        WorkScheduleSessionEnum.MORNING
    )

    afternoon_schedule = MagicMock(
        spec=WorkSchedule
    )
    afternoon_schedule.workDate = week_start
    afternoon_schedule.session = (
        WorkScheduleSessionEnum.AFTERNOON
    )

    mock_get_schedules.return_value = [
        morning_schedule,
        afternoon_schedule
    ]

    mock_get_appointments.return_value = []
    mock_get_config.return_value = mock_config

    result = dao.build_doctor_week_schedule(
        doctor_id=1,
        week_start=week_start
    )

    first_day = result[0]

    assert first_day["morning"] == morning_schedule

    assert first_day["afternoon"] == (
        afternoon_schedule
    )


# ============================================================
# QB-24 - APPOINTMENT CA SÁNG
# ============================================================

@patch("bookingonline.models.dao.get_system_config")
@patch("bookingonline.models.dao.get_doctor_appointments_by_week")
@patch("bookingonline.models.dao.get_doctor_work_schedules_by_week")
def test_qb24_morning_appointment(
    mock_get_schedules,
    mock_get_appointments,
    mock_get_config,
    week_start,
    mock_config
):
    """
    QB-24:
    Appointment trước afternoonStartTime
    phải thuộc danh sách morning_appointments.
    """

    appointment = MagicMock(
        spec=Appointment
    )

    appointment.scheduledDate = week_start
    appointment.scheduledTime = time(9, 0)

    mock_get_schedules.return_value = []

    mock_get_appointments.return_value = [
        appointment
    ]

    mock_get_config.return_value = mock_config

    result = dao.build_doctor_week_schedule(
        doctor_id=1,
        week_start=week_start
    )

    first_day = result[0]

    assert appointment in (
        first_day["morning_appointments"]
    )

    assert appointment not in (
        first_day["afternoon_appointments"]
    )


# ============================================================
# QB-24 - APPOINTMENT CA CHIỀU
# ============================================================

@patch("bookingonline.models.dao.get_system_config")
@patch("bookingonline.models.dao.get_doctor_appointments_by_week")
@patch("bookingonline.models.dao.get_doctor_work_schedules_by_week")
def test_qb24_afternoon_appointment(
    mock_get_schedules,
    mock_get_appointments,
    mock_get_config,
    week_start,
    mock_config
):
    """
    QB-24:
    Appointment từ afternoonStartTime trở đi
    phải thuộc afternoon_appointments.
    """

    appointment = MagicMock(
        spec=Appointment
    )

    appointment.scheduledDate = week_start
    appointment.scheduledTime = time(14, 0)

    mock_get_schedules.return_value = []

    mock_get_appointments.return_value = [
        appointment
    ]

    mock_get_config.return_value = mock_config

    result = dao.build_doctor_week_schedule(
        doctor_id=1,
        week_start=week_start
    )

    first_day = result[0]

    assert appointment not in (
        first_day["morning_appointments"]
    )

    assert appointment in (
        first_day["afternoon_appointments"]
    )


# ============================================================
# QB-24 - ĐÚNG RANH GIỚI CA CHIỀU
# ============================================================

@patch("bookingonline.models.dao.get_system_config")
@patch("bookingonline.models.dao.get_doctor_appointments_by_week")
@patch("bookingonline.models.dao.get_doctor_work_schedules_by_week")
def test_qb24_appointment_at_afternoon_start(
    mock_get_schedules,
    mock_get_appointments,
    mock_get_config,
    week_start,
    mock_config
):
    """
    QB-24:
    Appointment đúng bằng afternoonStartTime
    phải được tính là ca chiều.
    """

    appointment = MagicMock(
        spec=Appointment
    )

    appointment.scheduledDate = week_start
    appointment.scheduledTime = time(13, 30)

    mock_get_schedules.return_value = []

    mock_get_appointments.return_value = [
        appointment
    ]

    mock_get_config.return_value = mock_config

    result = dao.build_doctor_week_schedule(
        doctor_id=1,
        week_start=week_start
    )

    first_day = result[0]

    assert first_day["morning_appointments"] == []

    assert first_day["afternoon_appointments"] == [
        appointment
    ]