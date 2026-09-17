import json

from bookingonline.models import dao
from bookingonline.models.models import Specialization


def test_doctor_profile_detail_requires_login(client, make_doctor):
    make_doctor("d1")
    resp = client.get("/doctor-profile")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_doctor_profile_detail_blocks_patient_role_on_get(client, make_user, login):
    make_user("p1", password="Patient@123")
    login(client, "p1", "Patient@123")
    resp = client.get("/doctor-profile")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/")


def test_doctor_profile_detail_blocks_patient_role_on_patch(client, make_user, login):
    make_user("p1", password="Patient@123")
    login(client, "p1", "Patient@123")
    resp = client.patch("/doctor-profile", data={
        "licenseNumber": "HACK", "experienceYrs": "1", "fee": "1",
    })
    assert resp.status_code == 302


def test_doctor_profile_detail_get_shows_own_data(client, make_doctor, login):
    make_doctor("d1", license_number="BS-001")
    login(client, "d1", "Doctor@123")
    resp = client.get("/doctor-profile")
    assert resp.status_code == 200
    assert "BS-001" in resp.get_data(as_text=True)


def test_doctor_profile_detail_isolated_between_two_doctors(client, make_doctor, login):
    spec2 = Specialization(name="Tim mach")
    from bookingonline import db
    db.session.add(spec2)
    db.session.commit()

    make_doctor("d1", license_number="BS-001")
    make_doctor("d2", license_number="BS-002", spec=spec2)

    login(client, "d2", "Doctor@123")
    resp = client.get("/doctor-profile")
    body = resp.get_data(as_text=True)
    assert "BS-002" in body
    assert "BS-001" not in body


def test_doctor_profile_detail_patch_valid_updates_fields(client, make_doctor, login):
    d1, profile = make_doctor("d1", license_number="BS-001", fee=200000, experience_yrs=5)
    login(client, "d1", "Doctor@123")
    resp = client.patch("/doctor-profile", data={
        "licenseNumber": "BS-001-V2",
        "experienceYrs": "12",
        "fee": "275000",
        "description": "Mo ta moi",
        "bio": "Bio moi",
        "avatarUrl": "https://example.com/new.jpg",
    })
    assert resp.status_code == 200
    body = json.loads(resp.get_data(as_text=True))
    assert body["redirect"].endswith("/doctor-profile")

    refreshed = dao.get_doctor_profile_by_user(d1.id)
    assert refreshed.licenseNumber == "BS-001-V2"
    assert refreshed.experienceYrs == 12
    assert refreshed.fee == 275000.0
    assert refreshed.description == "Mo ta moi"
    assert refreshed.bio == "Bio moi"
    assert refreshed.avatarUrl == "https://example.com/new.jpg"


def test_doctor_profile_detail_patch_missing_license_number_returns_400(client, make_doctor, login):
    d1, profile = make_doctor("d1", license_number="BS-001")
    login(client, "d1", "Doctor@123")
    resp = client.patch("/doctor-profile", data={
        "licenseNumber": "", "experienceYrs": "5", "fee": "200000",
    })
    assert resp.status_code == 400
    refreshed = dao.get_doctor_profile_by_user(d1.id)
    assert refreshed.licenseNumber == "BS-001"


def test_doctor_profile_detail_patch_experience_out_of_range_returns_400(client, make_doctor, login):
    make_doctor("d1")
    login(client, "d1", "Doctor@123")
    resp = client.patch("/doctor-profile", data={
        "licenseNumber": "X", "experienceYrs": "71", "fee": "200000",
    })
    assert resp.status_code == 400


def test_doctor_profile_detail_patch_zero_fee_returns_400(client, make_doctor, login):
    make_doctor("d1")
    login(client, "d1", "Doctor@123")
    resp = client.patch("/doctor-profile", data={
        "licenseNumber": "X", "experienceYrs": "5", "fee": "0",
    })
    assert resp.status_code == 400


def test_doctor_profile_detail_patch_invalid_avatar_url_returns_400(client, make_doctor, login):
    make_doctor("d1")
    login(client, "d1", "Doctor@123")
    resp = client.patch("/doctor-profile", data={
        "licenseNumber": "X", "experienceYrs": "5", "fee": "200000",
        "avatarUrl": "javascript:alert(1)",
    })
    assert resp.status_code == 400


def test_doctor_profile_detail_patch_cannot_change_specialization(client, make_doctor, login, specialization):
    spec2 = Specialization(name="Tim mach")
    from bookingonline import db
    db.session.add(spec2)
    db.session.commit()

    d1, profile = make_doctor("d1", spec=specialization)
    login(client, "d1", "Doctor@123")
    client.patch("/doctor-profile", data={
        "licenseNumber": "X", "experienceYrs": "5", "fee": "200000",
        "specializationId": str(spec2.id),
    })
    refreshed = dao.get_doctor_profile_by_user(d1.id)
    assert refreshed.specializationId == specialization.id


def test_doctor_profile_detail_patch_cannot_change_rating_or_review_count(client, make_doctor, login):
    d1, profile = make_doctor("d1")
    profile.totalReview = 2
    profile.averageRating = 4.5
    from bookingonline import db
    db.session.commit()

    login(client, "d1", "Doctor@123")
    client.patch("/doctor-profile", data={
        "licenseNumber": "X", "experienceYrs": "5", "fee": "200000",
        "totalReview": "999", "averageRating": "5.0",
    })
    refreshed = dao.get_doctor_profile_by_user(d1.id)
    assert refreshed.totalReview == 2
    assert refreshed.averageRating == 4.5


def test_doctor_profile_detail_patch_updates_are_isolated_between_doctors(client, make_doctor, login):
    d1, _ = make_doctor("d1", license_number="BS-001")
    d2, _ = make_doctor("d2", license_number="BS-002")

    login(client, "d1", "Doctor@123")
    client.patch("/doctor-profile", data={
        "licenseNumber": "BS-001-CHANGED", "experienceYrs": "5", "fee": "200000",
    })

    d2_profile = dao.get_doctor_profile_by_user(d2.id)
    assert d2_profile.licenseNumber == "BS-002"
