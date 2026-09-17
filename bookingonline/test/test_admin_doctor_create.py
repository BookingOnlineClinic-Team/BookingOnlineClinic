import pytest
from unittest.mock import MagicMock, patch

from bookingonline import app
from bookingonline.models import dao


@pytest.fixture(autouse=True)
def app_context():
    with app.app_context():
        yield


# ---- Kiểm tra username đã tồn tại chưa ----

@patch("bookingonline.models.dao.db.session")
@patch("bookingonline.models.dao.User.query")
def test_username_taken_true(mock_query, mock_session):
    # Username đã có người dùng -> exists() trả True
    mock_session.query.return_value.exists.return_value = True
    mock_session.query.return_value = MagicMock()
    mock_session.query.return_value.scalar.return_value = True

    result = dao.is_username_taken("bacsi01")

    assert result is True


@patch("bookingonline.models.dao.db.session")
@patch("bookingonline.models.dao.User.query")
def test_username_taken_false(mock_query, mock_session):
    # Username chưa ai dùng -> False
    mock_session.query.return_value.scalar.return_value = False

    result = dao.is_username_taken("bacsi_moi")

    assert result is False


@patch("bookingonline.models.dao.db.session")
@patch("bookingonline.models.dao.User.query")
def test_username_taken_exclude_self(mock_query, mock_session):
    # Khi sửa hồ sơ, phải loại trừ chính user đang sửa (không tự báo trùng với chính mình)
    filtered = mock_query.filter.return_value
    mock_session.query.return_value.scalar.return_value = False

    dao.is_username_taken("bacsi01", exclude_user_id=5)

    # Phải có thêm 1 lần .filter() nữa để loại trừ id=5
    filtered.filter.assert_called_once()


# ---- Tạo tài khoản bác sĩ (User + DoctorProfile) ----

def sample_doctor_data():
    # Data mẫu dùng chung cho các test tạo bác sĩ
    return dict(
        name="Nguyen Van A", username="bacsi_a", password="123456",
        email="a@example.com", specialization_id=1,
        license_number="GPHN-001", experience_yrs=5, fee=200000,
    )


@patch("bookingonline.models.dao.db.session")
def test_create_doctor_account_success(mock_session):
    # Tạo thành công phải: add user -> flush -> add profile -> commit
    dao.create_doctor_account(**sample_doctor_data())

    assert mock_session.add.call_count == 2   # add user + add profile
    mock_session.flush.assert_called_once()
    mock_session.commit.assert_called_once()


@patch("bookingonline.models.dao.db.session")
def test_create_doctor_account_profile_uses_flushed_user_id(mock_session):
    # flush() xong thì user.id phải có giá trị, DoctorProfile phải lấy đúng userId đó
    def fake_flush():
        user_obj = mock_session.add.call_args_list[0].args[0]
        user_obj.id = 99  # giả lập DB tự sinh id sau khi flush

    mock_session.flush.side_effect = fake_flush

    dao.create_doctor_account(**sample_doctor_data())

    profile_obj = mock_session.add.call_args_list[1].args[0]
    assert profile_obj.userId == 99


@patch("bookingonline.models.dao.db.session")
def test_create_doctor_account_rollback_on_error(mock_session):
    # Nếu commit lỗi -> phải rollback, không được để dữ liệu tạo dở dang
    mock_session.commit.side_effect = Exception("DB error")

    with pytest.raises(Exception):
        dao.create_doctor_account(**sample_doctor_data())

    mock_session.rollback.assert_called_once()