"""
Hàm dùng chung cho toàn bộ hệ thống (KHÔNG được chứa route hay query DB trực tiếp
theo quy ước trong CLAUDE.md).
"""
from werkzeug.security import generate_password_hash, check_password_hash


def hash_password(raw_password):
    """Băm mật khẩu trước khi lưu DB. Không bao giờ lưu plaintext."""
    return generate_password_hash(raw_password)


def verify_password(raw_password, hashed_password):
    """So khớp mật khẩu người dùng nhập với hash đã lưu trong DB."""
    if not raw_password or not hashed_password:
        return False
    return check_password_hash(hashed_password, raw_password)
