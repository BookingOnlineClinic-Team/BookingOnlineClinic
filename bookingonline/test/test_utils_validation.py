from datetime import date, timedelta

import utils
from bookingonline.models.models import GenderEnum


def test_is_valid_phone_accepts_ten_digits_starting_with_zero():
    assert utils.is_valid_phone("0911111111") is True


def test_is_valid_phone_rejects_nine_digits():
    assert utils.is_valid_phone("091111111") is False


def test_is_valid_phone_rejects_eleven_digits():
    assert utils.is_valid_phone("09111111111") is False


def test_is_valid_phone_rejects_not_starting_with_zero():
    assert utils.is_valid_phone("1911111111") is False


def test_is_valid_phone_rejects_non_digit_characters():
    assert utils.is_valid_phone("091111abc1") is False


def test_is_valid_phone_rejects_empty_string():
    assert utils.is_valid_phone("") is False


def test_is_valid_birth_date_rejects_none():
    assert utils.is_valid_birth_date(None) is False


def test_is_valid_birth_date_rejects_future_date():
    assert utils.is_valid_birth_date(date.today() + timedelta(days=1)) is False


def test_is_valid_birth_date_accepts_today():
    assert utils.is_valid_birth_date(date.today()) is True


def test_is_valid_birth_date_rejects_over_120_years_ago():
    too_old = date(date.today().year - 121, 1, 1)
    assert utils.is_valid_birth_date(too_old) is False


def test_is_valid_birth_date_accepts_exactly_120_years_ago():
    exactly_120 = date(date.today().year - 120, date.today().month, date.today().day)
    assert utils.is_valid_birth_date(exactly_120) is True


def test_validate_patient_profile_form_requires_name():
    data, errors = utils.validate_patient_profile_form({"name": "", "phone": "0911111111"})
    assert "Vui lòng nhập họ tên" in errors


def test_validate_patient_profile_form_requires_valid_phone():
    data, errors = utils.validate_patient_profile_form({"name": "A", "phone": "123"})
    assert any("điện thoại" in e for e in errors)


def test_validate_patient_profile_form_rejects_invalid_gender():
    data, errors = utils.validate_patient_profile_form({
        "name": "A", "phone": "0911111111", "gender": "UNKNOWN",
    })
    assert any("Giới tính" in e for e in errors)


def test_validate_patient_profile_form_rejects_malformed_date():
    data, errors = utils.validate_patient_profile_form({
        "name": "A", "phone": "0911111111", "date_of_birth": "not-a-date",
    })
    assert any("Ngày sinh" in e for e in errors)


def test_validate_patient_profile_form_rejects_future_birth_date():
    future = (date.today() + timedelta(days=1)).isoformat()
    data, errors = utils.validate_patient_profile_form({
        "name": "A", "phone": "0911111111", "date_of_birth": future,
    })
    assert any("Ngày sinh" in e for e in errors)


def test_validate_patient_profile_form_valid_returns_no_errors_and_correct_data():
    data, errors = utils.validate_patient_profile_form({
        "name": "  Nguyen Van A  ",
        "phone": "0911111111",
        "gender": "MALE",
        "date_of_birth": "1990-05-20",
        "address": "12 Nguyen Trai",
    })
    assert errors == []
    assert data["name"] == "Nguyen Van A"
    assert data["phone"] == "0911111111"
    assert data["gender"] == GenderEnum.MALE
    assert data["date_of_birth"] == date(1990, 5, 20)
    assert data["address"] == "12 Nguyen Trai"


def test_validate_patient_profile_form_optional_fields_empty_returns_none():
    data, errors = utils.validate_patient_profile_form({"name": "A", "phone": "0911111111"})
    assert errors == []
    assert data["gender"] is None
    assert data["date_of_birth"] is None
    assert data["address"] is None


def test_validate_doctor_profile_form_requires_license_number():
    data, errors = utils.validate_doctor_profile_form({"experienceYrs": "5", "fee": "200000"})
    assert any("chứng chỉ" in e for e in errors)


def test_validate_doctor_profile_form_rejects_license_number_over_50_chars():
    data, errors = utils.validate_doctor_profile_form({
        "licenseNumber": "A" * 51, "experienceYrs": "5", "fee": "200000",
    })
    assert any("50 ký tự" in e for e in errors)


def test_validate_doctor_profile_form_accepts_license_number_exactly_50_chars():
    data, errors = utils.validate_doctor_profile_form({
        "licenseNumber": "A" * 50, "experienceYrs": "5", "fee": "200000",
    })
    assert errors == []


def test_validate_doctor_profile_form_requires_experience_yrs():
    data, errors = utils.validate_doctor_profile_form({"licenseNumber": "X", "fee": "200000"})
    assert any("kinh nghiệm" in e for e in errors)


def test_validate_doctor_profile_form_rejects_negative_experience_yrs():
    data, errors = utils.validate_doctor_profile_form({
        "licenseNumber": "X", "experienceYrs": "-1", "fee": "200000",
    })
    assert any("0-70" in e for e in errors)


def test_validate_doctor_profile_form_rejects_experience_yrs_over_70():
    data, errors = utils.validate_doctor_profile_form({
        "licenseNumber": "X", "experienceYrs": "71", "fee": "200000",
    })
    assert any("0-70" in e for e in errors)


def test_validate_doctor_profile_form_accepts_experience_yrs_boundaries():
    for value in ("0", "70"):
        data, errors = utils.validate_doctor_profile_form({
            "licenseNumber": "X", "experienceYrs": value, "fee": "200000",
        })
        assert errors == []


def test_validate_doctor_profile_form_rejects_non_integer_experience_yrs():
    data, errors = utils.validate_doctor_profile_form({
        "licenseNumber": "X", "experienceYrs": "abc", "fee": "200000",
    })
    assert any("số nguyên" in e for e in errors)


def test_validate_doctor_profile_form_rejects_zero_fee():
    data, errors = utils.validate_doctor_profile_form({
        "licenseNumber": "X", "experienceYrs": "5", "fee": "0",
    })
    assert any("lớn hơn 0" in e for e in errors)


def test_validate_doctor_profile_form_rejects_negative_fee():
    data, errors = utils.validate_doctor_profile_form({
        "licenseNumber": "X", "experienceYrs": "5", "fee": "-1",
    })
    assert any("lớn hơn 0" in e for e in errors)


def test_validate_doctor_profile_form_rejects_non_numeric_fee():
    data, errors = utils.validate_doctor_profile_form({
        "licenseNumber": "X", "experienceYrs": "5", "fee": "abc",
    })
    assert any("số" in e for e in errors)


def test_validate_doctor_profile_form_rejects_avatar_url_without_scheme():
    data, errors = utils.validate_doctor_profile_form({
        "licenseNumber": "X", "experienceYrs": "5", "fee": "200000",
        "avatarUrl": "ftp://example.com/a.jpg",
    })
    assert any("http" in e for e in errors)


def test_validate_doctor_profile_form_accepts_https_avatar_url():
    data, errors = utils.validate_doctor_profile_form({
        "licenseNumber": "X", "experienceYrs": "5", "fee": "200000",
        "avatarUrl": "https://example.com/a.jpg",
    })
    assert errors == []


def test_validate_doctor_profile_form_valid_returns_expected_data():
    data, errors = utils.validate_doctor_profile_form({
        "licenseNumber": "BS-001",
        "experienceYrs": "10",
        "fee": "250000",
        "description": "Mo ta",
        "bio": "Bio",
        "avatarUrl": "https://example.com/a.jpg",
    })
    assert errors == []
    assert data == {
        "license_number": "BS-001",
        "experience_yrs": 10,
        "fee": 250000.0,
        "description": "Mo ta",
        "bio": "Bio",
        "avatar_url": "https://example.com/a.jpg",
    }
