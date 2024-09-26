import pytest
from fastapi.testclient import TestClient
from main import app
from database import get_database, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture(scope='module')
def test_db():
    engine = create_engine('sqlite:///:memory:', connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture
def session(test_db):
    connection = test_db.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(session):
    app.dependency_overrides[get_database] = lambda: session
    return TestClient(app)

@pytest.fixture
def user():
    return {
        "username": "testuser",
        "password": "testpassword"
    }

def test_create_user(client, user):
    response = client.post(
        "/auth/signup",
        json=user,
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["username"] == user["username"]

def test_repeat_create_user(client, user):
    response = client.post("/auth/signup", json=user)
    assert response.status_code == 201, response.text

    response = client.post("/auth/signup", json=user)
    assert response.status_code == 409, response.text
    data = response.json()
    assert data["detail"] == "Account already exists"

def test_signup_invalid_username(client):
    response = client.post(
        "/auth/signup",
        json={"username": "", "password": "validpassword"},
    )
    assert response.status_code == 409

def test_signup_invalid_password(client):
    response = client.post(
        "/auth/signup",
        json={"username": "newuser", "password": ""},
    )
    assert response.status_code == 409
