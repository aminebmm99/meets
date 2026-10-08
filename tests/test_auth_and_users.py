from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Organization
from tests.conftest import TEST_PASSWORD


def test_registration_and_authenticated_me(client: TestClient, db_session: Session):
    organization = Organization(name="Acme")
    db_session.add(organization)
    db_session.commit()

    registration = client.post(
        "/users/",
        json={
            "email": "new-user@example.com",
            "name": "New User",
            "password": TEST_PASSWORD,
            "organization_id": organization.id,
        },
    )
    assert registration.status_code == 200
    assert registration.json()["email"] == "new-user@example.com"
    assert "password_hash" not in registration.json()

    login = client.post(
        "/auth/login",
        json={"email": "new-user@example.com", "password": TEST_PASSWORD},
    )
    assert login.status_code == 200
    assert login.json()["token_type"] == "bearer"
    assert login.json()["access_token"]

    me = client.get(
        "/users/me",
        headers={"Authorization": "Bearer " + login.json()["access_token"]},
    )
    assert me.status_code == 200
    assert me.json()["email"] == "new-user@example.com"


def test_duplicate_email_is_rejected(client: TestClient, db_session: Session):
    organization = Organization(name="Acme")
    db_session.add(organization)
    db_session.commit()
    user_data = {
        "email": "same@example.com",
        "name": "A User",
        "password": TEST_PASSWORD,
        "organization_id": organization.id,
    }

    assert client.post("/users/", json=user_data).status_code == 200
    duplicate = client.post("/users/", json=user_data)
    assert duplicate.status_code == 409


def test_login_rejects_invalid_password(client: TestClient, seeded):
    response = client.post(
        "/auth/login",
        json={"email": "owner@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401


def test_invalid_token_is_rejected(client: TestClient):
    response = client.get(
        "/users/me",
        headers={"Authorization": "Bearer not-a-valid-token"},
    )
    assert response.status_code == 401


def test_token_with_non_integer_subject_is_rejected(client: TestClient):
    import jwt

    from app.core.config import JWT_ALGORITHM, JWT_SECRET_KEY

    token = jwt.encode(
        {"sub": "not-an-id"},
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )
    response = client.get(
        "/users/me",
        headers={"Authorization": "Bearer " + token},
    )
    assert response.status_code == 401
