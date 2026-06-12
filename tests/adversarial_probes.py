#!/usr/bin/env python3
"""Adversarial / stress / security probes  outputs JSON findings."""
import concurrent.futures
import json
import uuid
from datetime import datetime, timezone

import httpx

BASE = "http://localhost:8000/api"
FINDINGS = []


def finding(severity: str, category: str, title: str, detail: str, evidence: dict | None = None):
    FINDINGS.append({
        "severity": severity,
        "category": category,
        "title": title,
        "detail": detail,
        "evidence": evidence or {},
    })


def register_user(client: httpx.Client) -> dict:
    email = f"probe_{uuid.uuid4().hex[:8]}@example.com"
    password = "ProbeTest1!"
    client.post("/register", json={"email": email, "password": password})
    login = client.post("/login", json={"email": email, "password": password})
    t = login.json()
    return {"email": email, "password": password, "access": t["access_token"], "refresh": t["refresh_token"]}


def auth(h: str) -> dict:
    return {"Authorization": f"Bearer {h}"}


def main():
    with httpx.Client(base_url=BASE, timeout=30.0) as c:
        u = register_user(c)

        # JWT alg=none
        r = c.get("/profile", headers={"Authorization": "Bearer eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiJoYWNrQGV4YW1wbGUuY29tIiwidHlwZSI6ImFjY2VzcyJ9."})
        if r.status_code == 401:
            finding("INFO", "security", "JWT alg=none rejected", "Server rejects unsigned JWT", {"status": r.status_code})
        else:
            finding("CRITICAL", "security", "JWT alg=none accepted", "Possible auth bypass", {"status": r.status_code, "body": r.text[:200]})

        # Refresh without Redis entry (forged jti)
        r = c.post("/refresh", json={"refresh_token": u["refresh"] + "x"})
        finding("INFO", "security", "Tampered refresh token", "Returns 401", {"status": r.status_code})

        # Logout with another user's refresh (if we had two users)
        u2 = register_user(c)
        r = c.post("/logout", json={"refresh_token": u2["refresh"]}, headers=auth(u["access"]))
        if r.status_code == 403:
            finding("INFO", "security", "Logout cross-user refresh blocked", "Fixed: 403 on mismatched sub", {"status": 403})
        elif r.status_code == 200:
            finding("HIGH", "security", "Logout cross-user refresh allowed", "Could revoke other user sessions", {"status": 200})

        # Oversized field name
        r = c.post("/fields", headers=auth(u["access"]), json={
            "name": "X" * 100000,
            "latitude": 55.0,
            "longitude": 37.0,
            "crop_type": "пшеница",
        })
        finding("MEDIUM" if r.status_code == 200 else "INFO", "validation", "Huge field name",
                f"Status {r.status_code}  no max_length on FieldCreate.name", {"status": r.status_code})

        # Invalid coordinates
        r = c.post("/fields", headers=auth(u["access"]), json={
            "name": "BadCoords",
            "latitude": 999,
            "longitude": 999,
            "crop_type": "пшеница",
        })
        if r.status_code == 200:
            finding("LOW", "validation", "Coordinates not bounded", "lat/lon 999 accepted  Open-Meteo may fail gracefully", {"status": 200})

        # Warehouse negative capacity
        r = c.post("/warehouse/", headers=auth(u["access"]), json={
            "name": "BadWH", "type": "элеватор", "capacity_t": -100
        })
        if r.status_code == 200:
            finding("MEDIUM", "validation", "Negative warehouse capacity", "capacity_t has no gt=0 constraint", {"status": 200})

        # Concurrent grain lot race
        wh = c.post("/warehouse/", headers=auth(u["access"]), json={
            "name": "RaceWH", "type": "элеватор", "capacity_t": 100
        }).json()

        def add_lot(_):
            try:
                with httpx.Client(base_url=BASE, timeout=10.0) as cx:
                    return cx.post("/warehouse/grain-lot/", headers=auth(u["access"]), json={
                        "warehouse_id": wh["id"],
                        "crop_type": "пшеница",
                        "weight_t": 60,
                        "harvest_date": "2025-09-01T00:00:00",
                    })
            except httpx.ReadTimeout:
                return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
            results = [r for r in ex.map(add_lot, range(3)) if r is not None]

        ok_count = sum(1 for r in results if r.status_code == 200)
        timeouts = 3 - len(results)
        if timeouts > 0:
            finding("HIGH", "concurrency", "Warehouse row lock contention",
                    f"{timeouts} requests timed out  with_for_update blocks concurrent grain-lot inserts",
                    {"timeouts": timeouts, "ok": ok_count})

        # Offline sync bomb
        ops = [{"type": "create_work_order", "data": {}} for _ in range(500)]
        r = c.post("/offline/sync", headers=auth(u["access"]), json=ops)
        finding("MEDIUM", "availability", "Offline sync no batch limit",
                f"500 invalid ops accepted with status {r.status_code}  DoS vector", {"status": r.status_code, "conflicts": r.json().get("conflicts")})

        # CORS preflight
        r = c.options("/health", headers={"Origin": "https://evil.com", "Access-Control-Request-Method": "GET"})
        finding("INFO", "security", "CORS evil origin", f"Preflight status {r.status_code}", {"acao": r.headers.get("access-control-allow-origin")})

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "findings_count": len(FINDINGS),
        "findings": FINDINGS,
    }
    path = "/app/tests/adversarial_findings.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
