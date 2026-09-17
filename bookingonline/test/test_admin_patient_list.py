import pytest
from unittest.mock import MagicMock, patch

from bookingonline import app
from bookingonline.models import dao
from bookingonline.models.models import User, UserRoleEnum


@pytest.fixture(autouse=True)
def app_context():
    with app.app_context():
        yield


# ---- Lấy danh sách bệnh nhân cho trang admin ----

@patch("bookingonline.models.dao.User.query")
def test_list_patients_success(mock_query):
    patient = MagicMock(spec=User)
    role_query = mock_query.filter.return_value
    role_query.order_by.return_value.all.return_value = [patient]

    result = dao.get_all_patients_admin()

    assert result == [patient]


@patch("bookingonline.models.dao.User.query")
def test_list_patients_filter_role_only(mock_query):
    # Không truyền keyword -> chỉ filter theo role PATIENT, gọi filter() đúng 1 lần
    role_query = mock_query.filter.return_value
    role_query.order_by.return_value.all.return_value = []

    dao.get_all_patients_admin()

    mock_query.filter.assert_called_once()
    condition = mock_query.filter.call_args.args[0]
    assert str(condition) == str(User.role == UserRoleEnum.PATIENT)


@patch("bookingonline.models.dao.User.query")
def test_list_patients_by_keyword(mock_query):
    # Có keyword -> phải filter thêm lần 2 (theo tên/username/email/phone)
    role_query = mock_query.filter.return_value
    keyword_query = MagicMock()
    role_query.filter.return_value = keyword_query
    keyword_query.order_by.return_value.all.return_value = []

    dao.get_all_patients_admin(keyword="  Tran Thi B  ")

    role_query.filter.assert_called_once()


@patch("bookingonline.models.dao.User.query")
def test_list_patients_empty_keyword_no_extra_filter(mock_query):
    # Keyword chỉ có khoảng trắng -> sau strip rỗng -> không thêm filter
    role_query = mock_query.filter.return_value
    role_query.order_by.return_value.all.return_value = []

    dao.get_all_patients_admin(keyword="   ")

    role_query.filter.assert_not_called()


# ---- Lấy user theo id ----

@patch("bookingonline.models.dao.User.query")
def test_get_user_by_id(mock_query):
    user = MagicMock(spec=User)
    mock_query.get.return_value = user

    result = dao.get_user_by_id(1)

    assert result == user
    mock_query.get.assert_called_once_with(1)