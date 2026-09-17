import pytest
from unittest.mock import MagicMock, patch
from datetime import time
from werkzeug.datastructures import MultiDict

from bookingonline import app
from bookingonline.models import dao
from bookingonline.models.models import SystemConfig
import utils


# FLASK APPLICATION CONTEXT


@pytest.fixture(autouse=True)
def app_context():
    # Flask-SQLAlchemy cần application context khi truy cập Model.query
    with app.app_context():
        yield


# FIXTURES


@pytest.fixture
def mock_config():
    config = MagicMock(spec=SystemConfig)
    config.maxAppointmentsPerDay = 1
    config.minimumBookingTime = 60
    config.minimumCancellationTime = 120
    return config


def build_valid_form(**overrides):
    # Form hợp lệ mặc định, mỗi test chỉ cần override 1-2 field
    # để tạo ra ca lỗi cần kiểm tra, đỡ phải khai báo lại toàn bộ form.
    base = {
        "workingDays": ["MONDAY", "TUESDAY", "WEDNESDAY"],
        "morningStartTime": "07:30",
        "morningEndTime": "11:30",
        "afternoonStartTime": "13:30",
        "afternoonEndTime": "17:30",
        "maxAppointmentsPerDay": "2",
        "minimumBookingTime": "60",
        "minimumCancellationTime": "120",
        "refundPercentagePatient": "100",
        "refundPercentageDoctor": "80",
    }
    base.update(overrides)

    # workingDays cần nhiều value cùng key -> phải build bằng list cặp
    # (key, value) rồi đưa vào MultiDict, giống hệt request.form thật của Flask
    items = []
    for key, value in base.items():
        if isinstance(value, list):
            for v in value:
                items.append((key, v))
        else:
            items.append((key, value))
    return MultiDict(items)



# LẤY CẤU HÌNH HỆ THỐNG (get_system_config)


@patch("bookingonline.models.dao.db.session.commit")
@patch("bookingonline.models.dao.db.session.add")
@patch("bookingonline.models.dao.SystemConfig.query")
def test_get_system_config_creates_default_when_missing(mock_query, mock_add, mock_commit):
    # Chưa từng có bản ghi config (id=1) trong DB -> phải tự tạo giá trị mặc định
    mock_query.get.return_value = None

    result = dao.get_system_config()

    mock_add.assert_called_once()
    mock_commit.assert_called_once()
    assert result.id == 1
    assert result.maxAppointmentsPerDay == 1


@patch("bookingonline.models.dao.SystemConfig.query")
def test_get_system_config_returns_existing_without_creating(mock_query, mock_config):
    # Đã có config sẵn -> trả về luôn, không được tạo bản ghi mới
    mock_query.get.return_value = mock_config

    result = dao.get_system_config()

    assert result == mock_config



# CẬP NHẬT CẤU HÌNH HỆ THỐNG (update_system_config)


@patch("bookingonline.models.dao.db.session.commit")
def test_update_system_config_sets_new_values(mock_commit, mock_config):
    dao.update_system_config(
        mock_config,
        maxAppointmentsPerDay=3,
        minimumBookingTime=90,
    )

    assert mock_config.maxAppointmentsPerDay == 3
    assert mock_config.minimumBookingTime == 90
    mock_commit.assert_called_once()


@patch("bookingonline.models.dao.db.session.commit")
def test_update_system_config_skips_none_values(mock_commit, mock_config):
    # Field giá trị None nghĩa là "không đổi" -> phải giữ nguyên giá trị cũ,
    # không được ghi đè thành None
    mock_config.maxAppointmentsPerDay = 5

    dao.update_system_config(mock_config, maxAppointmentsPerDay=None)

    assert mock_config.maxAppointmentsPerDay == 5
    mock_commit.assert_called_once()



# VALIDATE FORM - DỮ LIỆU HỢP LỆ


def test_validate_form_valid_data_has_no_errors():
    form = build_valid_form()

    data, errors = utils.validate_system_config_form(form)

    assert errors == []
    assert data["workingDays"] == "MONDAY,TUESDAY,WEDNESDAY"
    assert data["morningStartTime"] == time(7, 30)
    assert data["maxAppointmentsPerDay"] == 2


# ============================================================
# VALIDATE FORM - NGÀY LÀM VIỆC
# ============================================================

def test_validate_form_no_working_day_selected_is_error():
    form = build_valid_form(workingDays=[])

    data, errors = utils.validate_system_config_form(form)

    assert len(errors) == 1
    assert data["workingDays"] is None


def test_validate_form_invalid_working_day_is_ignored_not_error():
    # "FOOBAR" không phải ngày hợp lệ -> bị loại, nhưng vẫn còn MONDAY
    # nên không báo lỗi "chưa chọn ngày nào"
    form = build_valid_form(workingDays=["MONDAY", "FOOBAR"])

    data, errors = utils.validate_system_config_form(form)

    assert errors == []
    assert data["workingDays"] == "MONDAY"

# VALIDATE FORM - GIỜ LÀM VIỆC


def test_validate_form_missing_time_field_is_error():
    form = build_valid_form(morningStartTime="")

    data, errors = utils.validate_system_config_form(form)

    assert any("giờ bắt đầu ca sáng" in e for e in errors)
    assert data["morningStartTime"] is None


def test_validate_form_invalid_time_format_is_error():
    form = build_valid_form(morningStartTime="7h30")

    data, errors = utils.validate_system_config_form(form)

    assert any("không đúng định dạng giờ" in e for e in errors)
    assert data["morningStartTime"] is None


def test_validate_form_morning_end_before_start_is_error():
    form = build_valid_form(morningStartTime="11:00", morningEndTime="09:00")

    data, errors = utils.validate_system_config_form(form)

    assert any("Giờ kết thúc ca sáng" in e for e in errors)


def test_validate_form_afternoon_end_before_start_is_error():
    form = build_valid_form(afternoonStartTime="17:00", afternoonEndTime="14:00")

    data, errors = utils.validate_system_config_form(form)

    assert any("Giờ kết thúc ca chiều" in e for e in errors)


def test_validate_form_afternoon_overlaps_morning_is_error():
    # Ca chiều bắt đầu trước (hoặc ngay lúc) ca sáng kết thúc -> lỗi chồng ca
    form = build_valid_form(morningEndTime="14:00", afternoonStartTime="13:00")

    data, errors = utils.validate_system_config_form(form)

    assert any("Ca chiều phải bắt đầu sau" in e for e in errors)



# VALIDATE FORM - CÁC TRƯỜNG SỐ NGUYÊN


def test_validate_form_missing_integer_field_is_error():
    form = build_valid_form(maxAppointmentsPerDay="")

    data, errors = utils.validate_system_config_form(form)

    assert any("số lịch hẹn tối đa" in e for e in errors)
    assert data["maxAppointmentsPerDay"] is None


def test_validate_form_non_integer_field_is_error():
    form = build_valid_form(minimumBookingTime="abc")

    data, errors = utils.validate_system_config_form(form)

    assert any("phải là số nguyên" in e for e in errors)


def test_validate_form_integer_below_min_is_error():
    # maxAppointmentsPerDay yêu cầu tối thiểu là 1
    form = build_valid_form(maxAppointmentsPerDay="0")

    data, errors = utils.validate_system_config_form(form)

    assert any("phải nằm trong khoảng" in e for e in errors)


def test_validate_form_integer_above_max_is_error():
    # refundPercentagePatient tối đa 100
    form = build_valid_form(refundPercentagePatient="150")

    data, errors = utils.validate_system_config_form(form)

    assert any("phải nằm trong khoảng" in e for e in errors)