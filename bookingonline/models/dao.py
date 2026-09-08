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
