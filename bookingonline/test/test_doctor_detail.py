import pytest
from unittest.mock import MagicMock, patch

from bookingonline import app
from bookingonline.models import dao
from bookingonline.models.models import (
    DoctorProfile,
    Review,
    User,
    UserRoleEnum,
)


# ============================================================
# FLASK APPLICATION CONTEXT
# ============================================================

@pytest.fixture(autouse=True)
def app_context():
    """
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


@pytest.fixture
def mock_reviews():
    review_1 = MagicMock(spec=Review)
    review_1.id = 1
    review_1.doctorId = 1

    review_2 = MagicMock(spec=Review)
    review_2.id = 2
    review_2.doctorId = 1

    return [review_1, review_2]


# ============================================================
# QB-12 - XEM CHI TIẾT HỒ SƠ BÁC SĨ
# ============================================================

@patch("bookingonline.models.dao.DoctorProfile.query")
def test_qb12_get_doctor_detail_success(
    mock_query,
    mock_doctor
):
    """
    QB-12:
    Tìm thấy bác sĩ hợp lệ theo doctor_id.
    """

    joined_query = mock_query.join.return_value
    filtered_query = joined_query.filter.return_value

    filtered_query.first.return_value = mock_doctor

    result = dao.get_doctor_detail(1)

    assert result == mock_doctor

    mock_query.join.assert_called_once()

    join_args = mock_query.join.call_args.args

    assert join_args[0] == User

    assert str(join_args[1]) == str(
        DoctorProfile.userId == User.id
    )

    filtered_query.first.assert_called_once()


@patch("bookingonline.models.dao.DoctorProfile.query")
def test_qb12_doctor_not_found(
    mock_query
):
    """
    QB-12:
    doctor_id không tồn tại
    -> DAO trả về None.
    """

    joined_query = mock_query.join.return_value
    filtered_query = joined_query.filter.return_value

    filtered_query.first.return_value = None

    result = dao.get_doctor_detail(999)

    assert result is None


@patch("bookingonline.models.dao.DoctorProfile.query")
def test_qb12_filter_correct_doctor_id(
    mock_query
):
    """
    QB-12:
    Query phải tìm đúng doctor_id được truyền vào.
    """

    joined_query = mock_query.join.return_value
    filtered_query = joined_query.filter.return_value

    filtered_query.first.return_value = None

    dao.get_doctor_detail(15)

    conditions = joined_query.filter.call_args.args

    assert len(conditions) == 3

    assert str(
        conditions[0]
    ) == str(
        DoctorProfile.id == 15
    )


@patch("bookingonline.models.dao.DoctorProfile.query")
def test_qb12_only_active_doctor(
    mock_query
):
    """
    QB-12:
    Hồ sơ chi tiết chỉ được lấy khi:
    - User có role DOCTOR
    - User active = True
    """

    joined_query = mock_query.join.return_value
    filtered_query = joined_query.filter.return_value

    filtered_query.first.return_value = None

    dao.get_doctor_detail(1)

    conditions = joined_query.filter.call_args.args

    assert len(conditions) == 3

    assert str(
        conditions[1]
    ) == str(
        User.role == UserRoleEnum.DOCTOR
    )

    assert str(
        conditions[2]
    ) == str(
        User.active.is_(True)
    )


# ============================================================
# QB-13 - XEM ĐÁNH GIÁ BỆNH NHÂN VỚI BÁC SĨ
# ============================================================

@patch("bookingonline.models.dao.Review.query")
def test_qb13_get_reviews_success(
    mock_query,
    mock_reviews
):
    """
    QB-13:
    Lấy danh sách đánh giá của bác sĩ thành công.
    """

    filtered_query = mock_query.filter.return_value
    ordered_query = filtered_query.order_by.return_value

    ordered_query.all.return_value = mock_reviews

    result = dao.get_reviews_by_doctor(1)

    assert result == mock_reviews


@patch("bookingonline.models.dao.Review.query")
def test_qb13_no_reviews(
    mock_query
):
    """
    QB-13:
    Bác sĩ chưa có đánh giá
    -> trả về danh sách rỗng.
    """

    filtered_query = mock_query.filter.return_value
    ordered_query = filtered_query.order_by.return_value

    ordered_query.all.return_value = []

    result = dao.get_reviews_by_doctor(1)

    assert result == []


@pytest.mark.parametrize(
    "doctor_id",
    [
        1,
        2,
        10,
    ]
)
@patch("bookingonline.models.dao.Review.query")
def test_qb13_filter_reviews_by_doctor_id(
    mock_query,
    doctor_id
):
    """
    QB-13:
    Chỉ lấy review thuộc đúng doctor_id.
    """

    filtered_query = mock_query.filter.return_value
    ordered_query = filtered_query.order_by.return_value

    ordered_query.all.return_value = []

    dao.get_reviews_by_doctor(doctor_id)

    mock_query.filter.assert_called_once()

    condition = mock_query.filter.call_args.args[0]

    assert str(
        condition
    ) == str(
        Review.doctorId == doctor_id
    )


@patch("bookingonline.models.dao.Review.query")
def test_qb13_reviews_order_by_latest(
    mock_query
):
    """
    QB-13:
    Review phải được sắp xếp theo thời gian
    mới nhất trước.
    """

    filtered_query = mock_query.filter.return_value
    ordered_query = filtered_query.order_by.return_value

    ordered_query.all.return_value = []

    dao.get_reviews_by_doctor(1)

    filtered_query.order_by.assert_called_once()

    order_condition = (
        filtered_query
        .order_by
        .call_args
        .args[0]
    )

    assert str(
        order_condition
    ) == str(
        Review.time.desc()
    )