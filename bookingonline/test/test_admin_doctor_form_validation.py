import pytest
from unittest.mock import patch

from bookingonline import app
import utils


@pytest.fixture(autouse=True)
def app_context():
    with app.app_context():
        yield


def valid_form(**overrides):
    # Form hợp lệ mặc định, test nào cần sai field nào thì override field đó
    data = {
        "name": "Nguyen Van A",
        "email": "a@example.com",
        "phone": "0912345678",
        "gender": "MALE",
        "specializationId": "1",
        "licenseNumber": "GP-001",
        "experienceYrs": "5",
        "fee": "200000",
        "description": "",
        "bio": "",
        "avatarUrl": "",
        "username": "bacsi_a",
        "password": "123456",
        "confirmPassword": "123456",
    }
    data.update(overrides)
    return data


# ---- Form hợp lệ ----

@patch("utils.dao.is_username_taken", return_value=False)
@patch("utils.dao.get_specialization_by_id", return_value=True)
def test_valid_form_no_error(mock_spec, mock_username):
    data, errors = utils.validate_doctor_account_form(valid_form())

    assert errors == []
    assert data["name"] == "Nguyen Van A"
    assert data["experience_yrs"] == 5      # phải convert ra int
    assert data["fee"] == 200000.0          # phải convert ra float


# ---- Thiếu field bắt buộc ----

@patch("utils.dao.is_username_taken", return_value=False)
@patch("utils.dao.get_specialization_by_id", return_value=True)
@pytest.mark.parametrize("field", ["name", "licenseNumber", "experienceYrs", "fee"])
def test_missing_required_field(mock_spec, mock_username, field):
    data, errors = utils.validate_doctor_account_form(valid_form(**{field: ""}))

    assert len(errors) > 0


# ---- Email / SĐT sai định dạng ----

@patch("utils.dao.is_username_taken", return_value=False)
@patch("utils.dao.get_specialization_by_id", return_value=True)
def test_invalid_email(mock_spec, mock_username):
    data, errors = utils.validate_doctor_account_form(valid_form(email="khong-phai-email"))

    assert any("Email" in e for e in errors)


@patch("utils.dao.is_username_taken", return_value=False)
@patch("utils.dao.get_specialization_by_id", return_value=True)
def test_invalid_phone(mock_spec, mock_username):
    data, errors = utils.validate_doctor_account_form(valid_form(phone="123"))

    assert any("điện thoại" in e for e in errors)


# ---- Chuyên khoa ----

@patch("utils.dao.is_username_taken", return_value=False)
def test_specialization_not_exist(mock_username):
    with patch("utils.dao.get_specialization_by_id", return_value=None):
        data, errors = utils.validate_doctor_account_form(valid_form(specializationId="99"))

    assert any("Chuyên khoa" in e for e in errors)


# ---- Số năm kinh nghiệm / chi phí khám ----

@patch("utils.dao.is_username_taken", return_value=False)
@patch("utils.dao.get_specialization_by_id", return_value=True)
@pytest.mark.parametrize("experience_yrs", ["-1", "999", "abc"])
def test_invalid_experience_yrs(mock_spec, mock_username, experience_yrs):
    data, errors = utils.validate_doctor_account_form(valid_form(experienceYrs=experience_yrs))

    assert len(errors) > 0


@patch("utils.dao.is_username_taken", return_value=False)
@patch("utils.dao.get_specialization_by_id", return_value=True)
@pytest.mark.parametrize("fee", ["0", "-100", "abc"])
def test_invalid_fee(mock_spec, mock_username, fee):
    data, errors = utils.validate_doctor_account_form(valid_form(fee=fee))

    assert len(errors) > 0


# ---- Avatar URL ----

@patch("utils.dao.is_username_taken", return_value=False)
@patch("utils.dao.get_specialization_by_id", return_value=True)
def test_invalid_avatar_url(mock_spec, mock_username):
    data, errors = utils.validate_doctor_account_form(valid_form(avatarUrl="khong-phai-url"))

    assert any("Avatar" in e for e in errors)


# ---- Username / Password (chỉ validate khi tạo mới) ----

@patch("utils.dao.is_username_taken", return_value=True)
@patch("utils.dao.get_specialization_by_id", return_value=True)
def test_username_already_taken(mock_spec, mock_username):
    data, errors = utils.validate_doctor_account_form(valid_form())

    assert any("đã được sử dụng" in e for e in errors)


@patch("utils.dao.is_username_taken", return_value=False)
@patch("utils.dao.get_specialization_by_id", return_value=True)
def test_password_confirm_not_match(mock_spec, mock_username):
    data, errors = utils.validate_doctor_account_form(valid_form(confirmPassword="khac"))

    assert any("khớp" in e for e in errors)


def test_edit_mode_skip_username_password():
    # is_edit=True -> dù form không có username/password thì cũng không báo lỗi
    form = valid_form()
    form.pop("username")
    form.pop("password")
    form.pop("confirmPassword")

    with patch("utils.dao.get_specialization_by_id", return_value=True):
        data, errors = utils.validate_doctor_account_form(form, is_edit=True)

    assert errors == []
    assert "username" not in data