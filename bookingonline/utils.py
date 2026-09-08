"""
Hàm dùng chung cho toàn bộ hệ thống (KHÔNG được chứa route hay query DB trực tiếp
theo quy ước trong CLAUDE.md).
"""
import re
from datetime import date, datetime
from werkzeug.security import generate_password_hash, check_password_hash

# SĐT Việt Nam: 10 số, bắt đầu bằng 0 (03/05/07/08/09...)
PHONE_REGEX = re.compile(r'^0\d{9}$')


def hash_password(raw_password):
    """Băm mật khẩu trước khi lưu DB. Không bao giờ lưu plaintext."""
    return generate_password_hash(raw_password)


def verify_password(raw_password, hashed_password):
    """So khớp mật khẩu người dùng nhập với hash đã lưu trong DB."""
    if not raw_password or not hashed_password:
        return False
    return check_password_hash(hashed_password, raw_password)


def is_valid_phone(phone):
    """SĐT VN hợp lệ: đúng 10 số, bắt đầu bằng 0."""
    return bool(phone) and bool(PHONE_REGEX.match(phone.strip()))


def parse_date(date_str):
    """Parse chuỗi 'YYYY-MM-DD' (định dạng input type=date của HTML) thành
    date. Trả None nếu rỗng hoặc sai định dạng, không raise exception."""
    if not date_str or not date_str.strip():
        return None
    try:
        return datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
    except ValueError:
        return None


def is_valid_birth_date(d):
    """Ngày sinh hợp lệ: không ở tương lai, không quá vô lý (>120 tuổi)."""
    if d is None:
        return False
    if d > date.today():
        return False
    if d.year < date.today().year - 120:
        return False
    return True
