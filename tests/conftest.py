import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["DATABASE_URL"] = ""

from database import Base, get_db
from main import app
from models.user import User, UserRole
from models.instrument import Instrument, InstrumentStatus
from models.verification import Verification, VerificationStatus
from models.certificate import Certificate
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

TEST_DATABASE_URL = "sqlite://"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def admin_user(db):
    user = User(
        full_name="Test Admin",
        email="testadmin@test.com",
        phone="9000000001",
        hashed_password=pwd_context.hash("adminpass"[:72]),
        role=UserRole.ADMIN,
        organization="Test Org",
        address="Test Address",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def inspector_user(db):
    user = User(
        full_name="Test Inspector",
        email="testinspector@test.com",
        phone="9000000002",
        hashed_password=pwd_context.hash("inspectorpass"[:72]),
        role=UserRole.INSPECTOR,
        organization="Test Inspect Org",
        address="Test Inspect Address",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def owner_user(db):
    user = User(
        full_name="Test Owner",
        email="testowner@test.com",
        phone="9000000003",
        hashed_password=pwd_context.hash("ownerpass"[:72]),
        role=UserRole.OWNER,
        organization="Test Owner Org",
        address="Test Owner Address",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def seed_demo_accounts(db):
    demo_users = [
        {"full_name": "Admin User", "email": "admin@sih.com", "phone": "1111111111",
         "password": "admin123", "role": UserRole.ADMIN, "organization": "SIH Org", "address": "HQ"},
        {"full_name": "Inspector User", "email": "inspector@sih.com", "phone": "2222222222",
         "password": "inspector123", "role": UserRole.INSPECTOR, "organization": "Inspection Dept", "address": "Branch"},
        {"full_name": "Owner User", "email": "owner@sih.com", "phone": "3333333333",
         "password": "owner123", "role": UserRole.OWNER, "organization": "Owner Org", "address": "Owner Addr"},
    ]
    for u in demo_users:
        db.add(User(
            full_name=u["full_name"], email=u["email"], phone=u["phone"],
            hashed_password=pwd_context.hash(u["password"][:72]),
            role=u["role"], organization=u["organization"], address=u["address"],
        ))
    db.commit()


def get_auth_header(client, email, password):
    r = client.post(
        "/api/auth/login",
        data={"username": email, "password": password},
    )
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
