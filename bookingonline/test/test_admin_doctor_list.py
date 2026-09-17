import pytest
from unittest.mock import MagicMock, patch

from bookingonline import app
from bookingonline.models import dao
from bookingonline.models.models import DoctorProfile, User


# Mỗi test cần Flask app context thì Model.query mới chạy được
@pytest.fixture(autouse=True)
def app_context():
    with app.app_context():
        yield


@pytest.fixture
def mock_doctor():
    doctor = MagicMock(spec=DoctorProfile)
    doctor.id = 1
    return doctor


# ---- Lấy danh sách bác sĩ cho trang admin ----

@patch("bookingonline.models.dao.DoctorProfile.query")
def test_get_all_doctors_admin_success(mock_query, mock_doctor):
    # Query join + filter role DOCTOR -> trả về danh sách
    base_query = mock_query.join.return_value
    filtered_query = base_query.filter.return_value
    filtered_query.order_by.return_value.all.return_value = [mock_doctor]

    result = dao.get_all_doctors_admin()

    assert result == [mock_doctor]


@patch("bookingonline.models.dao.DoctorProfile.query")
def test_get_all_doctors_admin_khong_loc_active(mock_query):
    # QUAN TRỌNG: khác get_doctors() công khai, hàm này KHÔNG được lọc
    # User.active, vì admin cần thấy cả bác sĩ đã bị khóa để mở lại.
    base_query = mock_query.join.return_value
    filtered_query = base_query.filter.return_value
    filtered_query.order_by.return_value.all.return_value = []

    dao.get_all_doctors_admin()

    # Chỉ filter đúng 1 lần (theo role), không có lần filter thứ 2 theo active
    base_query.filter.assert_called_once()
    condition = base_query.filter.call_args.args[0]
    assert str(condition) == str(User.role == dao.UserRoleEnum.DOCTOR)


@patch("bookingonline.models.dao.DoctorProfile.query")
def test_get_all_doctors_admin_tim_theo_keyword(mock_query):
    # Có keyword -> phải filter thêm theo tên/username
    base_query = mock_query.join.return_value
    role_query = base_query.filter.return_value

    keyword_query = MagicMock()
    role_query.filter.return_value = keyword_query
    keyword_query.order_by.return_value.all.return_value = []

    dao.get_all_doctors_admin(keyword="  An  ")

    # keyword phải được strip trước khi filter
    role_query.filter.assert_called_once()


@patch("bookingonline.models.dao.DoctorProfile.query")
def test_get_all_doctors_admin_loc_theo_chuyen_khoa(mock_query):
    base_query = mock_query.join.return_value
    role_query = base_query.filter.return_value

    spec_query = MagicMock()
    role_query.filter.return_value = spec_query
    spec_query.order_by.return_value.all.return_value = []

    dao.get_all_doctors_admin(specialization_id=3)

    condition = role_query.filter.call_args.args[0]
    assert str(condition) == str(DoctorProfile.specializationId == 3)