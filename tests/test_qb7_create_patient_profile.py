import pytest

from bookingonline.models import dao


def test_create_profile_requires_login(client):
    resp = client.get("/new-profile")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_create_profile_get_redirects_to_select_profile(client, make_user, login):
    make_user("p1", password="Patient@123")
    login(client, "p1", "Patient@123")
    resp = client.get("/new-profile")
    assert resp.status_code == 302
    assert "/select-profile" in resp.headers["Location"]


def test_create_profile_post_missing_name_does_not_create_profile(client, make_user, login):
    p1 = make_user("p1", password="Patient@123")
    login(client, "p1", "Patient@123")
    client.post("/new-profile", data={"name": "", "phone": "0911111111"})
    assert dao.get_patient_profiles_by_owner(p1.id) == []


def test_create_profile_post_missing_phone_does_not_create_profile(client, make_user, login):
    p1 = make_user("p1", password="Patient@123")
    login(client, "p1", "Patient@123")
    client.post("/new-profile", data={"name": "Nguyen Van A", "phone": ""})
    assert dao.get_patient_profiles_by_owner(p1.id) == []


def test_create_profile_post_valid_creates_profile_owned_by_current_user(client, make_user, login):
    p1 = make_user("p1", password="Patient@123")
    login(client, "p1", "Patient@123")
    client.post("/new-profile", data={
        "name": "Nguyen Van A",
        "phone": "0911111111",
        "gender": "MALE",
        "date_of_birth": "1990-05-20",
        "address": "12 Nguyen Trai",
    })
    profiles = dao.get_patient_profiles_by_owner(p1.id)
    assert len(profiles) == 1
    assert profiles[0].name == "Nguyen Van A"
    assert profiles[0].phone == "0911111111"
    assert profiles[0].userId == p1.id


def test_create_profile_post_valid_redirects_to_select_specialization(client, make_user, login):
    make_user("p1", password="Patient@123")
    login(client, "p1", "Patient@123")
    resp = client.post("/new-profile", data={"name": "Nguyen Van A", "phone": "0911111111"})
    assert resp.status_code == 302
    assert "/specializations" in resp.headers["Location"]


def test_create_profile_post_does_not_validate_phone_format(client, make_user, login):
    p1 = make_user("p1", password="Patient@123")
    login(client, "p1", "Patient@123")
    resp = client.post("/new-profile", data={"name": "Nguyen Van A", "phone": "abc"})
    assert resp.status_code == 302
    profiles = dao.get_patient_profiles_by_owner(p1.id)
    assert len(profiles) == 1
    assert profiles[0].phone == "abc"


def test_create_profile_post_invalid_date_format_raises_value_error(client, make_user, login):
    make_user("p1", password="Patient@123")
    login(client, "p1", "Patient@123")
    with pytest.raises(ValueError):
        client.post("/new-profile", data={
            "name": "Nguyen Van A",
            "phone": "0911111111",
            "date_of_birth": "not-a-date",
        })


def test_create_profile_second_profile_for_same_owner_creates_two(client, make_user, login):
    p1 = make_user("p1", password="Patient@123")
    login(client, "p1", "Patient@123")
    client.post("/new-profile", data={"name": "Nguyen Van A", "phone": "0911111111"})
    client.post("/new-profile", data={"name": "Con Nguyen Van A", "phone": "0911111111"})
    profiles = dao.get_patient_profiles_by_owner(p1.id)
    assert len(profiles) == 2
