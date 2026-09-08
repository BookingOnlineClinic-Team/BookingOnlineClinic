"""
Nơi DUY NHẤT được phép tương tác trực tiếp với DB (query/CRUD qua SQLAlchemy).
Không đặt logic route, render_template, request.form... ở đây (theo CLAUDE.md).
"""
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
