import json

from bookingonline.models import dao


def test_patient_profile_detail_requires_login(client, make_user):
    p1 = make_user("p1", password="Patient@123")
    profile = dao.create_patient_profile(owner=p1, name="A", phone="0911111111")
    resp = client.get(f"/patient-profiles/{profile.id}")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_patient_profile_detail_get_shows_form_for_owner(client, make_user, login):
    p1 = make_user("p1", password="Patient@123")
    profile = dao.create_patient_profile(owner=p1, name="Nguyen Van A", phone="0911111111")
    login(client, "p1", "Patient@123")
    resp = client.get(f"/patient-profiles/{profile.id}")
    assert resp.status_code == 200
    assert "Nguyen Van A" in resp.get_data(as_text=True)


def test_patient_profile_detail_get_redirects_for_non_owner(client, make_user, login):
    p1 = make_user("p1", password="Patient@123")
    p2 = make_user("p2", password="Patient@123")
    profile = dao.create_patient_profile(owner=p1, name="Nguyen Van A", phone="0911111111")
    login(client, "p2", "Patient@123")
    resp = client.get(f"/patient-profiles/{profile.id}")
    assert resp.status_code == 302
    assert "/select-profile" in resp.headers["Location"]


def test_patient_profile_detail_get_redirects_for_nonexistent_id(client, make_user, login):
    make_user("p1", password="Patient@123")
    login(client, "p1", "Patient@123")
    resp = client.get("/patient-profiles/999999")
    assert resp.status_code == 302


def test_patient_profile_detail_patch_valid_updates_data(client, make_user, login):
    p1 = make_user("p1", password="Patient@123")
    profile = dao.create_patient_profile(owner=p1, name="Old Name", phone="0911111111")
    login(client, "p1", "Patient@123")
    resp = client.patch(f"/patient-profiles/{profile.id}", data={
        "name": "New Name",
        "phone": "0922222222",
        "gender": "FEMALE",
        "date_of_birth": "1995-01-01",
        "address": "New Address",
    })
    assert resp.status_code == 200
    body = json.loads(resp.get_data(as_text=True))
    assert body["redirect"].endswith("/select-profile")

    refreshed = dao.get_patient_profile_by_owner(profile.id, p1.id)
    assert refreshed.name == "New Name"
    assert refreshed.phone == "0922222222"
    assert refreshed.address == "New Address"


def test_patient_profile_detail_patch_missing_name_returns_400(client, make_user, login):
    p1 = make_user("p1", password="Patient@123")
    profile = dao.create_patient_profile(owner=p1, name="Old Name", phone="0911111111")
    login(client, "p1", "Patient@123")
    resp = client.patch(f"/patient-profiles/{profile.id}", data={
        "name": "", "phone": "0911111111",
    })
    assert resp.status_code == 400
    refreshed = dao.get_patient_profile_by_owner(profile.id, p1.id)
    assert refreshed.name == "Old Name"


def test_patient_profile_detail_patch_invalid_phone_returns_400(client, make_user, login):
    p1 = make_user("p1", password="Patient@123")
    profile = dao.create_patient_profile(owner=p1, name="Old Name", phone="0911111111")
    login(client, "p1", "Patient@123")
    resp = client.patch(f"/patient-profiles/{profile.id}", data={
        "name": "New Name", "phone": "123",
    })
    assert resp.status_code == 400
    refreshed = dao.get_patient_profile_by_owner(profile.id, p1.id)
    assert refreshed.phone == "0911111111"


def test_patient_profile_detail_patch_future_birth_date_returns_400(client, make_user, login):
    from datetime import date, timedelta
    p1 = make_user("p1", password="Patient@123")
    profile = dao.create_patient_profile(owner=p1, name="Old Name", phone="0911111111")
    login(client, "p1", "Patient@123")
    future = (date.today() + timedelta(days=1)).isoformat()
    resp = client.patch(f"/patient-profiles/{profile.id}", data={
        "name": "New Name", "phone": "0911111111", "date_of_birth": future,
    })
    assert resp.status_code == 400


def test_patient_profile_detail_patch_non_owner_returns_404(client, make_user, login):
    p1 = make_user("p1", password="Patient@123")
    p2 = make_user("p2", password="Patient@123")
    profile = dao.create_patient_profile(owner=p1, name="Old Name", phone="0911111111")
    login(client, "p2", "Patient@123")
    resp = client.patch(f"/patient-profiles/{profile.id}", data={
        "name": "HACKED", "phone": "0911111111",
    })
    assert resp.status_code == 404
    refreshed = dao.get_patient_profile_by_owner(profile.id, p1.id)
    assert refreshed.name == "Old Name"


def test_patient_profile_detail_patch_nonexistent_id_returns_404(client, make_user, login):
    make_user("p1", password="Patient@123")
    login(client, "p1", "Patient@123")
    resp = client.patch("/patient-profiles/999999", data={
        "name": "X", "phone": "0911111111",
    })
    assert resp.status_code == 404


def test_patient_profile_detail_patch_owned_profile_of_other_users_untouched(client, make_user, login):
    p1 = make_user("p1", password="Patient@123")
    p2 = make_user("p2", password="Patient@123")
    profile1 = dao.create_patient_profile(owner=p1, name="P1 Profile", phone="0911111111")
    dao.create_patient_profile(owner=p2, name="P2 Profile", phone="0922222222")
    login(client, "p1", "Patient@123")
    client.patch(f"/patient-profiles/{profile1.id}", data={
        "name": "P1 Updated", "phone": "0911111111",
    })
    p2_profiles = dao.get_patient_profiles_by_owner(p2.id)
    assert len(p2_profiles) == 1
    assert p2_profiles[0].name == "P2 Profile"
