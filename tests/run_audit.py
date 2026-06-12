#!/usr/bin/env python3
"""Full audit runner  executes pytest and writes JSON summary."""
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT_PATH = ROOT / "tests" / "audit_report.json"


def main():
    cmd = [
        sys.executable, "-m", "pytest",
        str(ROOT / "tests"),
        "-v", "--tb=short",
        "-q",
        "--json-report", "--json-report-file", str(REPORT_PATH.with_suffix(".pytest.json")),
    ]
    # json-report plugin may be missing  fallback to plain pytest
    try:
        subprocess.run([sys.executable, "-m", "pytest_jsonreport", "--version"], capture_output=True, check=True)
    except Exception:
        cmd = [sys.executable, "-m", "pytest", str(ROOT / "tests"), "-v", "--tb=line"]

    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "exit_code": proc.returncode,
        "stdout": proc.stdout[-50000:],
        "stderr": proc.stderr[-10000:],
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(proc.stdout)
    print(proc.stderr, file=sys.stderr)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
