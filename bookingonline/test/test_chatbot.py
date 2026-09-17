import pytest
from unittest.mock import MagicMock, patch
from datetime import date, time

from bookingonline import app
from bookingonline.models.models import (
    User,
    UserRoleEnum,
    ChatbotSession,
)


# ============================================================
# FLASK APPLICATION CONTEXT
# ============================================================

@pytest.fixture(autouse=True)
def app_context():
    # Flask-SQLAlchemy cần application context khi truy cập Model.query
    with app.app_context():
        yield


@pytest.fixture(autouse=True)
def disable_login():
    # Tắt kiểm tra đăng nhập trong quá trình chạy test chatbot
    old_value = app.config.get("LOGIN_DISABLED", False)
    app.config["LOGIN_DISABLED"] = True

    yield

    app.config["LOGIN_DISABLED"] = old_value


@pytest.fixture
def client():
    # Tạo Flask test client để kiểm thử các API chatbot
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_user():
    # Tài khoản bệnh nhân giả lập
    user = MagicMock(spec=User)
    user.id = 1
    user.name = "Nguyễn Văn A"
    user.active = True
    user.role = UserRoleEnum.PATIENT
    user.is_authenticated = True
    return user


@pytest.fixture
def mock_session():
    # Phiên chatbot giả lập
    session = MagicMock(spec=ChatbotSession)
    session.id = 1
    return session


@pytest.fixture
def mock_specialization():
    # Chuyên khoa giả lập
    specialization = MagicMock()
    specialization.id = 1
    specialization.name = "Nội tổng quát"
    specialization.description = "Khám các bệnh lý nội khoa"
    return specialization


@pytest.fixture
def mock_doctor():
    # Bác sĩ giả lập
    doctor = MagicMock()
    doctor.id = 1
    doctor.avatarUrl = None
    doctor.experienceYrs = 5
    doctor.averageRating = 4.5
    doctor.room = "A101"
    doctor.fee = 200000
    doctor.user.name = "Bác sĩ Nguyễn Văn B"
    return doctor


@pytest.fixture
def mock_slots():
    # Danh sách khung giờ trống giả lập
    return [
        {
            "work_schedule_id": 10,
            "work_date": date(2026, 9, 20),
            "session": "MORNING",
            "start": time(8, 0),
            "end": time(8, 30),
        }
    ]


# ============================================================
# CHATBOT INIT - KHỞI TẠO CHATBOT
# ============================================================

@patch("bookingonline.index.dao.get_specializations_brief")
@patch("bookingonline.index.dao.get_allowed_booking_dates")
def test_chatbot_init_returns_greeting_and_booking_dates(
    mock_get_dates,
    mock_get_specializations,
    client,
    mock_user,
):
    # Chatbot phải trả về lời chào, ngày khám và danh sách chuyên khoa
    mock_get_dates.return_value = [
        date(2026, 9, 20),
        date(2026, 9, 21),
    ]

    mock_get_specializations.return_value = [
        {
            "id": 1,
            "name": "Nội tổng quát",
            "description": "Khám nội khoa",
        }
    ]

    with patch("bookingonline.index.current_user", mock_user):
        response = client.get("/chatbot/init")

    assert response.status_code == 200

    data = response.get_json()

    assert "greeting" in data
    assert "dates" in data
    assert "specializations" in data
    assert len(data["dates"]) == 2
    assert data["specializations"][0]["name"] == "Nội tổng quát"


# ============================================================
# CHATBOT ANALYZE - KIỂM TRA DỮ LIỆU ĐẦU VÀO
# ============================================================

def test_chatbot_analyze_missing_message(client, mock_user):
    # Không có mô tả triệu chứng -> phải trả về lỗi 400
    with patch("bookingonline.index.current_user", mock_user):
        response = client.post(
            "/chatbot/analyze",
            json={
                "date": "2026-09-20"
            }
        )

    assert response.status_code == 400

    data = response.get_json()

    assert data["error"] == "invalid_input"


def test_chatbot_analyze_missing_date(client, mock_user):
    # Không có ngày khám -> phải trả về lỗi 400
    with patch("bookingonline.index.current_user", mock_user):
        response = client.post(
            "/chatbot/analyze",
            json={
                "message": "Tôi bị đau đầu"
            }
        )

    assert response.status_code == 400

    data = response.get_json()

    assert data["error"] == "invalid_input"


def test_chatbot_analyze_invalid_date_format(client, mock_user):
    # Ngày khám không đúng định dạng YYYY-MM-DD -> phải trả về lỗi 400
    with patch("bookingonline.index.current_user", mock_user):
        response = client.post(
            "/chatbot/analyze",
            json={
                "message": "Tôi bị đau đầu",
                "date": "20-09-2026",
            }
        )

    assert response.status_code == 400

    data = response.get_json()

    assert data["error"] == "invalid_input"


# ============================================================
# CHATBOT ANALYZE - LỖI KHI GỌI GEMINI
# ============================================================

@patch("bookingonline.index.dao.get_specializations_brief")
@patch("bookingonline.index.classify_specialization")
def test_chatbot_analyze_gemini_error(
    mock_classify,
    mock_get_specializations,
    client,
    mock_user,
):
    # Gemini gặp lỗi -> phải trả về HTTP 502
    mock_get_specializations.return_value = []

    from bookingonline.services.gemini_service import GeminiServiceError

    mock_classify.side_effect = GeminiServiceError("Gemini API error")

    with patch("bookingonline.index.current_user", mock_user):
        response = client.post(
            "/chatbot/analyze",
            json={
                "message": "Tôi bị đau đầu",
                "date": "2026-09-20",
            }
        )

    assert response.status_code == 502

    data = response.get_json()

    assert data["error"] == "ai_error"
    assert "fallback_url" in data


# ============================================================
# CHATBOT ANALYZE - KHÔNG XÁC ĐỊNH ĐƯỢC CHUYÊN KHOA
# ============================================================

@patch("bookingonline.index.dao.create_chatbot_session")
@patch("bookingonline.index.dao.get_specializations_brief")
@patch("bookingonline.index.classify_specialization")
def test_chatbot_analyze_need_manual_specialization(
    mock_classify,
    mock_get_specializations,
    mock_create_session,
    client,
    mock_user,
    mock_session,
):
    # AI không xác định được chuyên khoa -> yêu cầu bệnh nhân chọn thủ công
    mock_get_specializations.return_value = [
        {
            "id": 1,
            "name": "Nội tổng quát",
            "description": "Khám nội khoa",
        }
    ]

    mock_classify.return_value = {
        "specialization_id": None,
        "reason": "Không đủ thông tin để xác định chuyên khoa",
        "confidence": 0.3,
    }

    mock_create_session.return_value = mock_session

    with patch("bookingonline.index.current_user", mock_user):
        response = client.post(
            "/chatbot/analyze",
            json={
                "message": "Tôi cảm thấy không khỏe",
                "date": "2026-09-20",
            }
        )

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == "NEED_MANUAL_SPECIALIZATION"
    assert data["session_id"] == mock_session.id
    assert "specializations" in data

    mock_create_session.assert_called_once()


# ============================================================
# CHATBOT ANALYZE - KHÔNG CÓ LỊCH TRỐNG
# ============================================================

@patch("bookingonline.index.dao.get_doctors_with_slots_by_specialization_on_date")
@patch("bookingonline.index.dao.get_specialization_by_id")
@patch("bookingonline.index.dao.create_chatbot_session")
@patch("bookingonline.index.dao.get_specializations_brief")
@patch("bookingonline.index.classify_specialization")
def test_chatbot_analyze_no_available_slots(
    mock_classify,
    mock_get_specializations,
    mock_create_session,
    mock_get_specialization,
    mock_get_doctors,
    client,
    mock_user,
    mock_session,
    mock_specialization,
):
    # Không có bác sĩ hoặc lịch trống -> trả về NO_SLOTS
    mock_get_specializations.return_value = []

    mock_classify.return_value = {
        "specialization_id": 1,
        "reason": "Triệu chứng phù hợp với chuyên khoa nội tổng quát",
        "confidence": 0.9,
    }

    mock_create_session.return_value = mock_session
    mock_get_specialization.return_value = mock_specialization
    mock_get_doctors.return_value = []

    with patch("bookingonline.index.current_user", mock_user):
        response = client.post(
            "/chatbot/analyze",
            json={
                "message": "Tôi bị đau đầu",
                "date": "2026-09-20",
            }
        )

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == "NO_SLOTS"
    assert data["session_id"] == mock_session.id
    assert data["specialization"]["id"] == mock_specialization.id


# ============================================================
# CHATBOT ANALYZE - GỢI Ý BÁC SĨ THÀNH CÔNG
# ============================================================

@patch("bookingonline.index.dao.add_chatbot_doctor_suggestion")
@patch("bookingonline.index.dao.get_doctors_with_slots_by_specialization_on_date")
@patch("bookingonline.index.dao.get_specialization_by_id")
@patch("bookingonline.index.dao.create_chatbot_session")
@patch("bookingonline.index.dao.get_specializations_brief")
@patch("bookingonline.index.classify_specialization")
def test_chatbot_analyze_returns_doctors_and_slots(
    mock_classify,
    mock_get_specializations,
    mock_create_session,
    mock_get_specialization,
    mock_get_doctors,
    mock_add_suggestion,
    client,
    mock_user,
    mock_session,
    mock_specialization,
    mock_doctor,
    mock_slots,
):
    # AI xác định được chuyên khoa và có bác sĩ còn lịch trống
    mock_get_specializations.return_value = []

    mock_classify.return_value = {
        "specialization_id": 1,
        "reason": "Triệu chứng phù hợp với chuyên khoa nội tổng quát",
        "confidence": 0.95,
    }

    mock_create_session.return_value = mock_session
    mock_get_specialization.return_value = mock_specialization

    mock_get_doctors.return_value = [
        {
            "doctor": mock_doctor,
            "slots": mock_slots,
        }
    ]

    mock_suggestion = MagicMock()
    mock_suggestion.id = 100
    mock_add_suggestion.return_value = mock_suggestion

    with patch("bookingonline.index.current_user", mock_user):
        response = client.post(
            "/chatbot/analyze",
            json={
                "message": "Tôi bị đau đầu",
                "date": "2026-09-20",
            }
        )

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == "OK"
    assert data["session_id"] == mock_session.id
    assert data["specialization"]["id"] == 1
    assert data["confidence"] == 0.95
    assert len(data["doctors"]) == 1
    assert data["doctors"][0]["doctor_id"] == mock_doctor.id
    assert data["doctors"][0]["suggestion_id"] == 100

    mock_add_suggestion.assert_called_once()


# ============================================================
# CHATBOT MANUAL SPECIALIZATION - DỮ LIỆU ĐẦU VÀO
# ============================================================

def test_chatbot_manual_specialization_missing_data(client, mock_user):
    # Không truyền specialization_id -> phải trả về lỗi 400
    with patch("bookingonline.index.current_user", mock_user):
        response = client.post(
            "/chatbot/manual-specialization",
            json={
                "date": "2026-09-20"
            }
        )

    assert response.status_code == 400

    data = response.get_json()

    assert data["error"] == "invalid_input"


@patch("bookingonline.index.dao.get_specialization_by_id")
def test_chatbot_manual_specialization_not_found(
    mock_get_specialization,
    client,
    mock_user,
):
    # specialization_id không tồn tại -> phải trả về lỗi 400
    mock_get_specialization.return_value = None

    with patch("bookingonline.index.current_user", mock_user):
        response = client.post(
            "/chatbot/manual-specialization",
            json={
                "specialization_id": 999,
                "date": "2026-09-20",
            }
        )

    assert response.status_code == 400

    data = response.get_json()

    assert data["error"] == "invalid_input"


# ============================================================
# CHATBOT MANUAL SPECIALIZATION - KHÔNG CÓ LỊCH TRỐNG
# ============================================================

@patch("bookingonline.index.dao.get_doctors_with_slots_by_specialization_on_date")
@patch("bookingonline.index.dao.create_chatbot_session")
@patch("bookingonline.index.dao.get_specialization_by_id")
def test_chatbot_manual_specialization_no_available_slots(
    mock_get_specialization,
    mock_create_session,
    mock_get_doctors,
    client,
    mock_user,
    mock_session,
    mock_specialization,
):
    # Chuyên khoa hợp lệ nhưng không có bác sĩ còn lịch trống
    mock_get_specialization.return_value = mock_specialization
    mock_create_session.return_value = mock_session
    mock_get_doctors.return_value = []

    with patch("bookingonline.index.current_user", mock_user):
        response = client.post(
            "/chatbot/manual-specialization",
            json={
                "specialization_id": 1,
                "date": "2026-09-20",
            }
        )

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == "NO_SLOTS"
    assert data["session_id"] == mock_session.id
    assert data["specialization"]["id"] == mock_specialization.id


# ============================================================
# CHATBOT MANUAL SPECIALIZATION - CHỌN CHUYÊN KHOA THÀNH CÔNG
# ============================================================

@patch("bookingonline.index.dao.add_chatbot_doctor_suggestion")
@patch("bookingonline.index.dao.get_doctors_with_slots_by_specialization_on_date")
@patch("bookingonline.index.dao.create_chatbot_session")
@patch("bookingonline.index.dao.get_specialization_by_id")
def test_chatbot_manual_specialization_returns_doctors(
    mock_get_specialization,
    mock_create_session,
    mock_get_doctors,
    mock_add_suggestion,
    client,
    mock_user,
    mock_session,
    mock_specialization,
    mock_doctor,
    mock_slots,
):
    # Bệnh nhân chọn chuyên khoa thủ công và có bác sĩ còn lịch trống
    mock_get_specialization.return_value = mock_specialization
    mock_create_session.return_value = mock_session

    mock_get_doctors.return_value = [
        {
            "doctor": mock_doctor,
            "slots": mock_slots,
        }
    ]

    mock_suggestion = MagicMock()
    mock_suggestion.id = 200
    mock_add_suggestion.return_value = mock_suggestion

    with patch("bookingonline.index.current_user", mock_user):
        response = client.post(
            "/chatbot/manual-specialization",
            json={
                "specialization_id": 1,
                "date": "2026-09-20",
            }
        )

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == "OK"
    assert data["session_id"] == mock_session.id
    assert data["specialization"]["id"] == mock_specialization.id
    assert len(data["doctors"]) == 1
    assert data["doctors"][0]["doctor_id"] == mock_doctor.id
    assert data["doctors"][0]["suggestion_id"] == 200

    mock_add_suggestion.assert_called_once()