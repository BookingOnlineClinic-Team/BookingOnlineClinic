import pytest
from unittest.mock import MagicMock, patch

from bookingonline import app
from bookingonline.models import dao
from bookingonline.models.models import (
    DoctorProfile,
    User,
    UserRoleEnum,
)


# ============================================================
# FLASK APPLICATION CONTEXT
# ============================================================

@pytest.fixture(autouse=True)
def app_context():
    """
    Tạo Flask application context cho mỗi unit test.

    Flask-SQLAlchemy cần application context
    khi truy cập Model.query.
    """
    with app.app_context():
        yield


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def mock_doctor():
    doctor = MagicMock(spec=DoctorProfile)
    doctor.id = 1
    return doctor

# ============================================================
# QB-10 - XEM DANH SÁCH BÁC SĨ
# ============================================================

@patch("bookingonline.models.dao.DoctorProfile.query")
def test_qb10_get_doctors_success(
    mock_query,
    mock_doctor
):
    """
    QB-10:
    Lấy danh sách bác sĩ thành công.
    """

    doctor_2 = MagicMock(spec=DoctorProfile)
    doctor_2.id = 2

    expected = [
        mock_doctor,
        doctor_2
    ]

    base_query = mock_query.join.return_value
    filtered_query = base_query.filter.return_value

    filtered_query.order_by.return_value.all.return_value = expected

    result = dao.get_doctors()

    assert result == expected


@patch("bookingonline.models.dao.DoctorProfile.query")
def test_qb10_get_doctors_empty(
    mock_query
):
    """
    QB-10:
    Không có bác sĩ -> trả về danh sách rỗng.
    """

    base_query = mock_query.join.return_value
    filtered_query = base_query.filter.return_value

    filtered_query.order_by.return_value.all.return_value = []

    result = dao.get_doctors()

    assert result == []


@patch("bookingonline.models.dao.DoctorProfile.query")
def test_qb10_filter_doctor_role_and_active(
    mock_query
):
    """
    QB-10:
    Danh sách chỉ lấy:
    - User có role DOCTOR
    - User đang active
    """

    base_query = mock_query.join.return_value
    filtered_query = base_query.filter.return_value

    filtered_query.order_by.return_value.all.return_value = []

    dao.get_doctors()

    base_query.filter.assert_called_once()

    conditions = base_query.filter.call_args.args

    assert len(conditions) == 2

    assert str(
        conditions[0]
    ) == str(
        User.role == UserRoleEnum.DOCTOR
    )

    assert str(
        conditions[1]
    ) == str(
        User.active.is_(True)
    )


# ============================================================
# QB-14 - TÌM KIẾM BÁC SĨ THEO TÊN
# ============================================================

@pytest.mark.parametrize(
    "keyword, expected_keyword",
    [
        (
            "Nguyen Van An",
            "Nguyen Van An"
        ),
        (
            "   Nguyen Van An   ",
            "Nguyen Van An"
        ),
        (
            "An",
            "An"
        ),
    ]
)
@patch("bookingonline.models.dao.DoctorProfile.query")
def test_qb14_search_doctor_by_name(
    mock_query,
    keyword,
    expected_keyword
):
    """
    QB-14:
    Tìm bác sĩ theo tên.

    Đồng thời kiểm tra keyword được strip
    khoảng trắng đầu/cuối.
    """

    base_query = mock_query.join.return_value
    active_query = base_query.filter.return_value

    keyword_query = MagicMock()

    active_query.filter.return_value = keyword_query

    keyword_query.order_by.return_value.all.return_value = []

    dao.get_doctors(
        keyword=keyword
    )

    active_query.filter.assert_called_once()

    condition = (
        active_query
        .filter
        .call_args
        .args[0]
    )

    expected_condition = User.name.ilike(
        f"%{expected_keyword}%"
    )

    assert str(condition) == str(
        expected_condition
    )


@patch("bookingonline.models.dao.DoctorProfile.query")
def test_qb14_empty_keyword(
    mock_query
):
    """
    QB-14:
    Keyword chỉ có khoảng trắng.

    Sau strip -> keyword rỗng
    -> không thêm filter theo tên.
    """

    base_query = mock_query.join.return_value
    active_query = base_query.filter.return_value

    active_query.order_by.return_value.all.return_value = []

    result = dao.get_doctors(
        keyword="     "
    )

    assert result == []

    active_query.filter.assert_not_called()


# ============================================================
# QB-14 - LỌC THEO CHUYÊN KHOA
# ============================================================

@pytest.mark.parametrize(
    "specialization_id",
    [
        1,
        2,
        3,
    ]
)
@patch("bookingonline.models.dao.DoctorProfile.query")
def test_qb14_filter_by_specialization(
    mock_query,
    specialization_id
):
    """
    QB-14:
    Lọc bác sĩ theo specialization_id.
    """

    base_query = mock_query.join.return_value
    active_query = base_query.filter.return_value

    specialization_query = MagicMock()

    active_query.filter.return_value = (
        specialization_query
    )

    specialization_query.order_by.return_value.all.return_value = []

    dao.get_doctors(
        specialization_id=specialization_id
    )

    active_query.filter.assert_called_once()

    condition = (
        active_query
        .filter
        .call_args
        .args[0]
    )

    expected_condition = (
        DoctorProfile.specializationId
        == specialization_id
    )

    assert str(condition) == str(
        expected_condition
    )


# ============================================================
# QB-14 - TÌM THEO TÊN + CHUYÊN KHOA
# ============================================================

@patch("bookingonline.models.dao.DoctorProfile.query")
def test_qb14_search_name_and_specialization(
    mock_query,
    mock_doctor
):
    """
    QB-14:
    Kết hợp:
    - tìm theo tên
    - lọc theo chuyên khoa
    """

    base_query = mock_query.join.return_value
    active_query = base_query.filter.return_value

    name_query = MagicMock()
    specialization_query = MagicMock()

    # Filter theo tên
    active_query.filter.return_value = (
        name_query
    )

    # Sau đó filter theo chuyên khoa
    name_query.filter.return_value = (
        specialization_query
    )

    specialization_query.order_by.return_value.all.return_value = [
        mock_doctor
    ]

    result = dao.get_doctors(
        keyword="An",
        specialization_id=2
    )

    assert result == [mock_doctor]

    # Kiểm tra điều kiện tên
    name_condition = (
        active_query
        .filter
        .call_args
        .args[0]
    )

    assert str(
        name_condition
    ) == str(
        User.name.ilike("%An%")
    )

    # Kiểm tra điều kiện chuyên khoa
    specialization_condition = (
        name_query
        .filter
        .call_args
        .args[0]
    )

    assert str(
        specialization_condition
    ) == str(
        DoctorProfile.specializationId == 2
    )


# ============================================================
# QB-14 - KHÔNG TÌM THẤY
# ============================================================

@patch("bookingonline.models.dao.DoctorProfile.query")
def test_qb14_search_no_result(
    mock_query
):
    """
    QB-14:
    Không có bác sĩ phù hợp
    -> trả về [].
    """

    base_query = mock_query.join.return_value
    active_query = base_query.filter.return_value

    keyword_query = MagicMock()

    active_query.filter.return_value = (
        keyword_query
    )

    keyword_query.order_by.return_value.all.return_value = []

    result = dao.get_doctors(
        keyword="TenKhongTonTai"
    )

    assert result == []