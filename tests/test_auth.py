"""Stage 1-2: Auth, validation, health."""
import time

import httpx
import pytest

from tests.conftest import auth_headers


class TestHealth:
    def test_health_ok(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert body["postgres"] == "ok"
        assert body["redis"] == "ok"


class TestAuthRegistration:
    def test_weak_password_rejected(self, client):
        r = client.post("/register", json={"email": "weak@test.local", "password": "1234567"})
        assert r.status_code == 422

    def test_duplicate_email_conflict(self, client, user_a):
        r = client.post("/register", json={"email": user_a["email"], "password": "Duplicate1!"})
        assert r.status_code == 409

    def test_invalid_email_rejected(self, client):
        r = client.post("/register", json={"email": "not-an-email", "password": "ValidPass1!"})
        assert r.status_code == 422


class TestAuthLogin:
    def test_wrong_password_401(self, client, user_a):
        r = client.post("/login", json={"email": user_a["email"], "password": "WrongPass1!"})
        assert r.status_code == 401

class TestAuthTokens:
    def test_profile_requires_auth(self, client):
        assert client.get("/profile").status_code == 401

    def test_profile_ok(self, client, user_a):
        r = client.get("/profile", headers=auth_headers(user_a))
        assert r.status_code == 200
        assert r.json()["email"] == user_a["email"]

    def test_refresh_rotation(self, client, user_a):
        old_refresh = user_a["refresh_token"]
        r = client.post("/refresh", json={"refresh_token": old_refresh})
        assert r.status_code == 200
        new_tokens = r.json()
        assert new_tokens["access_token"] != user_a["access_token"]
        # Old refresh must be revoked
        r2 = client.post("/refresh", json={"refresh_token": old_refresh})
        assert r2.status_code == 401

    def test_access_token_rejected_on_refresh(self, client, user_a):
        r = client.post("/refresh", json={"refresh_token": user_a["access_token"]})
        assert r.status_code == 401

    def test_tampered_jwt_rejected(self, client):
        r = client.post("/refresh", json={"refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.invalid"})
        assert r.status_code == 401

    def test_logout_revokes_refresh(self, client, user_a):
        login = client.post("/login", json={"email": user_a["email"], "password": user_a["password"]})
        assert login.status_code == 200, login.text
        tokens = login.json()
        h = {"Authorization": f"Bearer {tokens['access_token']}"}
        r = client.post("/logout", json={"refresh_token": tokens["refresh_token"]}, headers=h)
        assert r.status_code == 200
        r2 = client.post("/refresh", json={"refresh_token": tokens["refresh_token"]})
        assert r2.status_code == 401
