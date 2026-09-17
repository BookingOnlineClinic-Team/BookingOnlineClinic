import pytest
from unittest.mock import MagicMock, patch

from bookingonline import app
from bookingonline.models import dao
from bookingonline.models.models import Specialization
import utils

# FLASK APPLICATION CONTEXT
@pytest.fixture(autouse=True)
def app_context():
    # Flask-SQLAlchemy cần application context
    # khi truy cập Model.query.
    with app.app_context():
        yield



# FIXTURES
@pytest.fixture
def mock_specialization():
    spec = MagicMock(spec=Specialization)
    spec.id = 1
    spec.name = "Tim mạch"
    spec.icon = "heart-pulse"
    spec.description = "Khám và điều trị bệnh tim mạch"
    spec.active = True
    return spec



# LẤY DANH SÁCH CHUYÊN KHOA (get_all_specializations)

@patch("bookingonline.models.dao.Specialization.query")
def test_get_all_specializations_active_only(mock_query):
    """
    Mặc định (active_only=True) chỉ lấy chuyên khoa đang mở,
    dùng cho trang đặt lịch của bệnh nhân.
    """
    filtered_query = mock_query.filter.return_value
    ordered_query = filtered_query.order_by.return_value
    ordered_query.all.return_value = []

    dao.get_all_specializations()

    # Có filter theo active = True
    mock_query.filter.assert_called_once()


@patch("bookingonline.models.dao.Specialization.query")
def test_get_all_specializations_include_inactive(mock_query):
    # active_only=False (trang admin) -> không filter,
    # lấy luôn cả chuyên khoa đã khóa.
    ordered_query = mock_query.order_by.return_value
    ordered_query.all.return_value = []

    dao.get_all_specializations(active_only=False)

    # Không được gọi filter khi active_only=False
    mock_query.filter.assert_not_called()

# KIỂM TRA TRÙNG TÊN (is_specialization_name_taken)


@patch("bookingonline.models.dao.db.session.query")
@patch("bookingonline.models.dao.Specialization.query")
def test_name_taken_returns_true_when_exists(mock_query, mock_session_query):
    # Tên đã tồn tại -> trả về True.
    mock_session_query.return_value.scalar.return_value = True

    result = dao.is_specialization_name_taken("Tim mạch")

    assert result is True


@patch("bookingonline.models.dao.db.session.query")
@patch("bookingonline.models.dao.Specialization.query")
def test_name_taken_returns_false_when_not_exists(mock_query, mock_session_query):
    # Tên chưa tồn tại -> trả về False.
    mock_session_query.return_value.scalar.return_value = False

    result = dao.is_specialization_name_taken("Chuyên khoa mới")

    assert result is False


@patch("bookingonline.models.dao.db.session.query")
@patch("bookingonline.models.dao.Specialization.query")
def test_name_taken_excludes_current_id_when_editing(mock_query, mock_session_query):
    # Khi sửa chuyên khoa, phải loại trừ chính nó ra khỏi
    # kiểm tra trùng tên (nếu không sẽ luôn báo trùng với chính nó).
    filtered = mock_query.filter.return_value
    mock_session_query.return_value.scalar.return_value = False

    dao.is_specialization_name_taken("Tim mạch", exclude_id=5)

    # filter được gọi 2 lần: 1 lần so tên, 1 lần loại trừ id=5
    assert mock_query.filter.call_count == 1
    filtered.filter.assert_called_once()



# THÊM CHUYÊN KHOA (create_specialization)


@patch("bookingonline.models.dao.db.session.commit")
@patch("bookingonline.models.dao.db.session.add")
def test_create_specialization_success(mock_add, mock_commit):
    # Tạo chuyên khoa mới, mặc định active=True.
    result = dao.create_specialization(
        name="  Da liễu  ",
        icon="sparkles",
        description="  Khám da  ",
    )

    mock_add.assert_called_once()
    new_spec = mock_add.call_args.args[0]

    # Tên/mô tả phải được strip() khoảng trắng thừa
    assert new_spec.name == "Da liễu"
    assert new_spec.description == "Khám da"
    assert new_spec.icon == "sparkles"
    assert new_spec.active is True

    mock_commit.assert_called_once()
    assert result == new_spec


@patch("bookingonline.models.dao.db.session.commit")
@patch("bookingonline.models.dao.db.session.add")
def test_create_specialization_default_icon(mock_add, mock_commit):
    # Không truyền icon -> tự gán 'stethoscope'
    dao.create_specialization(name="Nội tổng quát")

    new_spec = mock_add.call_args.args[0]
    assert new_spec.icon == "stethoscope"



# SỬA CHUYÊN KHOA (update_specialization)


@patch("bookingonline.models.dao.db.session.commit")
def test_update_specialization_changes_fields(mock_commit, mock_specialization):
    """Cập nhật đúng field và gọi commit."""
    dao.update_specialization(
        mock_specialization,
        name="Tim mạch cấp cứu",
        icon="activity",
        description="Mô tả mới",
    )

    assert mock_specialization.name == "Tim mạch cấp cứu"
    assert mock_specialization.icon == "activity"
    assert mock_specialization.description == "Mô tả mới"
    mock_commit.assert_called_once()


# ============================================================
# KHÓA / MỞ KHÓA CHUYÊN KHOA (toggle_specialization_active)
# ============================================================

@patch("bookingonline.models.dao.db.session.commit")
def test_toggle_active_locks_when_currently_open(mock_commit, mock_specialization):
    """Đang mở -> bấm khóa -> active thành False."""
    mock_specialization.active = True

    dao.toggle_specialization_active(mock_specialization)

    assert mock_specialization.active is False
    mock_commit.assert_called_once()


@patch("bookingonline.models.dao.db.session.commit")
def test_toggle_active_unlocks_when_currently_locked(mock_commit, mock_specialization):
    # Đang khóa -> bấm mở khóa -> active thành True.
    mock_specialization.active = False

    dao.toggle_specialization_active(mock_specialization)

    assert mock_specialization.active is True
    mock_commit.assert_called_once()



# ĐẾM SỐ BÁC SĨ THUỘC CHUYÊN KHOA (count_doctors_in_specialization)


@patch("bookingonline.models.dao.DoctorProfile.query")
def test_count_doctors_in_specialization(mock_query):
    # Đếm đúng số bác sĩ đang gắn với 1 chuyên khoa.
    mock_query.filter_by.return_value.count.return_value = 3

    result = dao.count_doctors_in_specialization(1)

    assert result == 3
    mock_query.filter_by.assert_called_once_with(specializationId=1)


# XÓA CHUYÊN KHOA (delete_specialization)

@patch("bookingonline.models.dao.count_doctors_in_specialization")
def test_delete_blocked_when_has_doctors(mock_count, mock_specialization):
    # Còn bác sĩ trực thuộc -> KHÔNG được xóa,
    # trả về (False, thông báo lỗi).
    mock_count.return_value = 2

    ok, message = dao.delete_specialization(mock_specialization)

    assert ok is False
    assert message is not None
    assert "bác sĩ" in message


@patch("bookingonline.models.dao.db.session.commit")
@patch("bookingonline.models.dao.db.session.delete")
@patch("bookingonline.models.dao.count_doctors_in_specialization")
def test_delete_success_when_no_doctors(mock_count, mock_delete, mock_commit, mock_specialization):
    # Không còn bác sĩ nào -> xóa thành công.
    mock_count.return_value = 0

    ok, message = dao.delete_specialization(mock_specialization)

    assert ok is True
    assert message is None
    mock_delete.assert_called_once_with(mock_specialization)
    mock_commit.assert_called_once()

# VALIDATE FORM THÊM/SỬA CHUYÊN KHOA (utils.validate_specialization_form)

@patch("utils.dao.is_specialization_name_taken")
def test_validate_form_valid_data_has_no_errors(mock_taken):
    # Dữ liệu hợp lệ -> không có lỗi nào.
    mock_taken.return_value = False

    form = {"name": "Nhi khoa", "description": "Khám nhi"}
    data, errors = utils.validate_specialization_form(form)

    assert errors == []
    assert data["name"] == "Nhi khoa"



@patch("utils.dao.is_specialization_name_taken")
def test_validate_form_empty_name_is_error(mock_taken):
    # Bỏ trống tên chuyên khoa -> báo lỗi.
    mock_taken.return_value = False

    form = {"name": "  ", "icon": "stethoscope", "description": ""}
    data, errors = utils.validate_specialization_form(form)

    assert len(errors) == 1


@patch("utils.dao.is_specialization_name_taken")
def test_validate_form_name_too_long_is_error(mock_taken):
    # Tên chuyên khoa vượt quá 120 ký tự -> báo lỗi.
    mock_taken.return_value = False

    form = {"name": "A" * 121, "icon": "stethoscope", "description": ""}
    data, errors = utils.validate_specialization_form(form)

    assert len(errors) == 1


@patch("utils.dao.is_specialization_name_taken")
def test_validate_form_duplicate_name_is_error(mock_taken):
    # Tên chuyên khoa đã tồn tại trong DB -> báo lỗi trùng.
    mock_taken.return_value = True

    form = {"name": "Tim mạch", "icon": "heart-pulse", "description": ""}
    data, errors = utils.validate_specialization_form(form)

    assert len(errors) == 1


@patch("utils.dao.is_specialization_name_taken")
def test_validate_form_description_too_long_is_error(mock_taken):
    # Mô tả vượt quá 255 ký tự -> báo lỗi.
    mock_taken.return_value = False

    form = {"name": "Nhi khoa", "icon": "baby", "description": "A" * 256}
    data, errors = utils.validate_specialization_form(form)

    assert len(errors) == 1


@patch("utils.dao.is_specialization_name_taken")
def test_validate_form_exclude_id_passed_to_dao(mock_taken):
    # Khi sửa chuyên khoa, exclude_id phải được truyền xuống
    # dao.is_specialization_name_taken để không tự báo trùng với chính nó.
    mock_taken.return_value = False

    form = {"name": "Tim mạch", "icon": "heart-pulse", "description": ""}
    utils.validate_specialization_form(form, exclude_id=5)

    mock_taken.assert_called_once_with("Tim mạch", exclude_id=5)