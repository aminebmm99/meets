from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.dependencies import get_db
from app.core.database import Base
from app.core.security import hash_password
from app.main import app
from app.models import Meeting, Organization, Participant, User


TEST_PASSWORD = "test-password-123"
TEST_PASSWORD_HASH = hash_password(TEST_PASSWORD)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    testing_session = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )
    db = testing_session()

    def override_get_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield db
    finally:
        app.dependency_overrides.clear()
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def seeded(db_session: Session):
    first_org = Organization(name="Northwind")
    second_org = Organization(name="Contoso")
    db_session.add_all([first_org, second_org])
    db_session.flush()

    owner = User(
        email="owner@example.com",
        name="Meeting Organizer",
        password_hash=TEST_PASSWORD_HASH,
        organization_id=first_org.id,
    )
    participant_user = User(
        email="participant@example.com",
        name="Meeting Participant",
        password_hash=TEST_PASSWORD_HASH,
        organization_id=first_org.id,
    )
    outsider = User(
        email="outsider@example.com",
        name="Outside User",
        password_hash=TEST_PASSWORD_HASH,
        organization_id=second_org.id,
    )
    db_session.add_all([owner, participant_user, outsider])
    db_session.flush()

    meeting = Meeting(
        title="Weekly planning",
        description="Plan the week",
        organizer_id=owner.id,
        organization_id=first_org.id,
    )
    db_session.add(meeting)
    db_session.flush()

    participant = Participant(
        meeting_id=meeting.id,
        user_id=participant_user.id,
        status="invited",
    )
    db_session.add(participant)
    db_session.commit()

    return {
        "organization": first_org,
        "other_organization": second_org,
        "owner": owner,
        "participant_user": participant_user,
        "outsider": outsider,
        "meeting": meeting,
        "participant": participant,
    }


@pytest.fixture
def auth_headers(client: TestClient):
    def make_headers(email: str = "owner@example.com"):
        response = client.post(
            "/auth/login",
            json={"email": email, "password": TEST_PASSWORD},
        )
        assert response.status_code == 200
        return {"Authorization": "Bearer " + response.json()["access_token"]}

    return make_headers
