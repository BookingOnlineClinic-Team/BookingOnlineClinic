from bookingonline.models import dao
from bookingonline.models.models import PatientHealthProfile, UserRoleEnum


def test_login_get_renders_form_when_anonymous(client):
    resp = client.get("/login")
    assert resp.status_code == 200


def test_login_redirects_authenticated_patient_to_select_profile(client, make_user, login):
    make_user("p1", password="Patient@123")
    login(client, "p1", "Patient@123")
    resp = client.get("/login")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/select-profile")


def test_login_redirects_authenticated_doctor_to_doctor_profile(client, make_doctor, login):
    make_doctor("d1")
    login(client, "d1", "Doctor@123")
    resp = client.get("/login")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/doctor-profile")


def test_login_post_correct_credentials_redirects_patient(client, make_user):
    make_user("p1", password="Patient@123")
    resp = client.post("/login", data={"username": "p1", "password": "Patient@123"})
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/select-profile")


def test_login_post_correct_credentials_redirects_doctor(client, make_doctor):
    make_doctor("d1")
    resp = client.post("/login", data={"username": "d1", "password": "Doctor@123"})
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/doctor-profile")


def test_login_post_wrong_password_does_not_authenticate(client, make_user):
    make_user("p1", password="Patient@123")
    resp = client.post("/login", data={"username": "p1", "password": "wrong"})
    assert resp.status_code == 200
    resp2 = client.get("/select-profile")
    assert resp2.status_code == 302
    assert "/login" in resp2.headers["Location"]


def test_login_post_unknown_username_does_not_authenticate(client):
    resp = client.post("/login", data={"username": "ghost", "password": "x"})
    assert resp.status_code == 200


def test_logout_clears_session(client, make_user, login):
    make_user("p1", password="Patient@123")
    login(client, "p1", "Patient@123")
    client.get("/logout")
    resp = client.get("/select-profile")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_select_profile_requires_login(client):
    resp = client.get("/select-profile")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_select_profile_lists_only_current_user_profiles(client, make_user, login):
    p1 = make_user("p1", password="Patient@123")
    p2 = make_user("p2", password="Patient@123")
    dao.create_patient_profile(owner=p1, name="Nguyen Van A", phone="0911111111")
    dao.create_patient_profile(owner=p2, name="Tran Thi B", phone="0922222222")

    login(client, "p1", "Patient@123")
    resp = client.get("/select-profile")
    body = resp.get_data(as_text=True)
    assert "Nguyen Van A" in body
    assert "Tran Thi B" not in body


def test_select_profile_post_search_not_found_flashes_and_redirects(client, make_user, login):
    make_user("p1", password="Patient@123")
    login(client, "p1", "Patient@123")
    resp = client.post("/select-profile", data={"phone": "0900000000", "name": "Nobody"})
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/select-profile")


def test_select_profile_post_search_found_redirects_to_specialization(client, make_user, login):
    p1 = make_user("p1", password="Patient@123")
    profile = dao.create_patient_profile(owner=p1, name="Nguyen Van A", phone="0911111111")
    login(client, "p1", "Patient@123")
    resp = client.post("/select-profile", data={"phone": "0911111111", "name": "Nguyen Van A"})
    assert resp.status_code == 302
    assert f"profile_id={profile.id}" in resp.headers["Location"]


def test_get_patient_profiles_by_owner_returns_empty_list_for_new_user(make_user):
    p1 = make_user("p1", password="Patient@123")
    assert dao.get_patient_profiles_by_owner(p1.id) == []


def test_verify_login_returns_none_for_wrong_password(make_user):
    make_user("p1", password="Patient@123")
    assert dao.verify_login("p1", "wrong") is None


def test_verify_login_returns_user_for_correct_password(make_user):
    p1 = make_user("p1", password="Patient@123")
    result = dao.verify_login("p1", "Patient@123")
    assert result is not None
    assert result.id == p1.id


def test_verify_login_with_role_filter_rejects_mismatched_role(make_user):
    make_user("p1", password="Patient@123", role=UserRoleEnum.PATIENT)
    assert dao.verify_login("p1", "Patient@123", role=UserRoleEnum.DOCTOR) is None
