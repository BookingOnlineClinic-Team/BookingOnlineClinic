"""
Nơi DUY NHẤT được phép tương tác trực tiếp với DB (query/CRUD qua SQLAlchemy).
Không đặt logic route, render_template, request.form... ở đây (theo CLAUDE.md).
"""
from bookingonline import db
from bookingonline.models.models import User, PatientHealthProfile


def get_user_by_id(user_id):
    return User.query.get(int(user_id))


def get_user_by_username(username):
    if not username:
        return None
    return (User.query
            .filter(User.username == username, User.active == True)
            .first())


def get_health_profiles_by_user(user_id):
    return (PatientHealthProfile.query
            .filter(PatientHealthProfile.userId == user_id)
            .order_by(PatientHealthProfile.id)
            .all())


def create_health_profile(user_id, name, phone, gender=None, date_of_birth=None, address=None):
    """Tạo hồ sơ khám mới thuộc sở hữu của user_id (đặt cho chính mình hoặc
    đặt hộ người khác đều gọi hàm này, chỉ khác giá trị name/dateOfBirth...).
    Validate dữ liệu (format sđt, ngày sinh...) phải làm ở utils/index TRƯỚC
    khi gọi hàm này — dao chỉ chịu trách nhiệm ghi DB."""
    profile = PatientHealthProfile(
        userId=user_id,
        name=name,
        phone=phone,
        gender=gender,
        dateOfBirth=date_of_birth,
        address=address,
    )
    db.session.add(profile)
    db.session.commit()
    return profile


def get_health_profile_by_id(profile_id, user_id):
    """Lấy 1 hồ sơ khám theo id, CHỈ trả về nếu hồ sơ đó thuộc sở hữu của
    user_id — bắt buộc để tránh IDOR (user A sửa được hồ sơ của user B chỉ
    bằng cách đổi id trên URL). Trả None nếu không tồn tại hoặc không phải
    chủ sở hữu."""
    return (PatientHealthProfile.query
            .filter(PatientHealthProfile.id == profile_id, PatientHealthProfile.userId == user_id)
            .first())


def update_health_profile(profile, name, phone, gender=None, date_of_birth=None, address=None):
    """Cập nhật 1 hồ sơ khám đã lấy sẵn qua get_health_profile_by_id (đã được
    xác nhận đúng chủ sở hữu ở đó). Validate phải làm ở utils/index TRƯỚC khi
    gọi hàm này."""
    profile.name = name
    profile.phone = phone
    profile.gender = gender
    profile.dateOfBirth = date_of_birth
    profile.address = address
    db.session.commit()
    return profile
