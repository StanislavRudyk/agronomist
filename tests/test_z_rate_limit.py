"""Rate limit test isolated  must run after other auth tests (alphabetical z_ prefix)."""
import uuid

import pytest


class TestAuthRateLimit:
    def test_login_rate_limit(self, client):
        email = f"ratelimit_{uuid.uuid4().hex[:8]}@example.com"
        client.post("/register", json={"email": email, "password": "RateLimit1!"})
        for _ in range(6):
            client.post("/login", json={"email": email, "password": "WrongPass1!"})
        r = client.post("/login", json={"email": email, "password": "WrongPass1!"})
        assert r.status_code == 429
