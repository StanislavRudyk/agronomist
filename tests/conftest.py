"""Fixtures for Agronomist API audit tests."""
import os
import time
import uuid

import httpx
import pytest

BASE_URL = os.getenv("TEST_API_URL", "http://localhost:8000/api")


def _strong_password() -> str:
    return "AuditTest1!"


def _register_and_login(client, email: str, password: str) -> dict:
    r = client.post("/register", json={"email": email, "password": password})
    assert r.status_code == 201, r.text
    for attempt in range(5):
        login = client.post("/login", json={"email": email, "password": password})
        if login.status_code == 200:
            tokens = login.json()
            return {
                "email": email,
                "password": password,
                "access_token": tokens["access_token"],
                "refresh_token": tokens["refresh_token"],
            }
        if login.status_code == 429:
            time.sleep(12)
            continue
        assert False, login.text
    pytest.fail("Login rate-limited during test setup")


@pytest.fixture(scope="session")
def client():
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as c:
        yield c


@pytest.fixture(scope="session")
def user_a(client):
    email = f"audit_a_{uuid.uuid4().hex[:8]}@example.com"
    return _register_and_login(client, email, _strong_password())


@pytest.fixture(scope="session")
def user_b(client):
    email = f"audit_b_{uuid.uuid4().hex[:8]}@example.com"
    return _register_and_login(client, email, _strong_password())


def auth_headers(user: dict) -> dict:
    return {"Authorization": f"Bearer {user['access_token']}"}
