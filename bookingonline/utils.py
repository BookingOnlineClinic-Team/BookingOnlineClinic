"""
Hàm dùng chung cho toàn bộ hệ thống (KHÔNG được chứa route hay query DB trực tiếp
theo quy ước trong CLAUDE.md).
"""
import re
from datetime import date, datetime
from werkzeug.security import generate_password_hash, check_password_hash
from bookingonline.models.models import GenderEnum

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


def validate_health_profile_form(form):
    """Validate + parse dữ liệu form tạo/sửa hồ sơ khám (dùng chung cho cả 2
    route để không lặp code / lặp lỗi validate).
    Trả về (data, errors): data là dict giá trị đã parse sẵn để truyền thẳng
    vào dao (chỉ đáng tin khi errors rỗng), errors là list message tiếng Việt
    để flash cho user."""
    name = form.get('name', '').strip()
    phone = form.get('phone', '').strip()
    gender_raw = form.get('gender', '').strip()
    dob_raw = form.get('dateOfBirth', '').strip()
    address = form.get('address', '').strip()

    errors = []
    if not name:
        errors.append('Vui lòng nhập họ tên.')

    if not is_valid_phone(phone):
        errors.append('Số điện thoại không hợp lệ (10 số, bắt đầu bằng 0).')

    gender = None
    if gender_raw:
        try:
            gender = GenderEnum(gender_raw)
        except ValueError:
            errors.append('Giới tính không hợp lệ.')

    date_of_birth = None
    if dob_raw:
        date_of_birth = parse_date(dob_raw)
        if date_of_birth is None:
            errors.append('Ngày sinh không đúng định dạng.')
        elif date_of_birth > date.today():
            errors.append('Ngày sinh không được ở tương lai.')
        elif not is_valid_birth_date(date_of_birth):
            errors.append('Ngày sinh không hợp lệ (quá xa so với hiện tại).')

    data = {
        'name': name,
        'phone': phone,
        'gender': gender,
        'date_of_birth': date_of_birth,
        'address': address or None,
    }
    return data, errors


def validate_doctor_profile_form(form):
    """Validate + parse dữ liệu form sửa hồ sơ bác sĩ.
    Trả về (data, errors) — cùng convention với validate_health_profile_form."""
    license_number = form.get('licenseNumber', '').strip()
    experience_yrs_raw = form.get('experienceYrs', '').strip()
    fee_raw = form.get('fee', '').strip()
    description = form.get('description', '').strip()
    bio = form.get('bio', '').strip()
    avatar_url = form.get('avatarUrl', '').strip()

    errors = []

    if not license_number:
        errors.append('Vui lòng nhập số chứng chỉ hành nghề.')
    elif len(license_number) > 50:
        errors.append('Số chứng chỉ hành nghề tối đa 50 ký tự.')

    experience_yrs = None
    if not experience_yrs_raw:
        errors.append('Vui lòng nhập số năm kinh nghiệm.')
    else:
        try:
            experience_yrs = int(experience_yrs_raw)
            if experience_yrs < 0 or experience_yrs > 70:
                errors.append('Số năm kinh nghiệm không hợp lệ (0-70).')
        except ValueError:
            errors.append('Số năm kinh nghiệm phải là số nguyên.')

    fee = None
    if not fee_raw:
        errors.append('Vui lòng nhập chi phí khám.')
    else:
        try:
            fee = float(fee_raw)
            if fee <= 0:
                errors.append('Chi phí khám phải lớn hơn 0.')
        except ValueError:
            errors.append('Chi phí khám phải là số.')

    if avatar_url and not (avatar_url.startswith('http://') or avatar_url.startswith('https://')):
        errors.append('Avatar URL phải bắt đầu bằng http:// hoặc https://.')

    data = {
        'license_number': license_number,
        'experience_yrs': experience_yrs,
        'fee': fee,
        'description': description or None,
        'bio': bio or None,
        'avatar_url': avatar_url or None,
    }
    return data, errors
