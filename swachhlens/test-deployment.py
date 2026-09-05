"""Deployment readiness test script."""
import os
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
import json
import urllib.request
import sys

BASE = "http://127.0.0.1:8000"
FRONTEND = "http://127.0.0.1:3000"
passed = 0
failed = 0

def api(method, path, data=None, token=None):
    url = BASE + path
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req)
        return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read()
        try:
            return e.code, json.loads(body) if body else {}
        except Exception:
            return e.code, {}

def check(label, ok):
    global passed, failed
    status = "PASS" if ok else "FAIL"
    if ok: passed += 1
    else: failed += 1
    print(f"  [{status}] {label}")

print("=" * 60)
print("DEPLOYMENT READINESS AUDIT")
print("=" * 60)

# 1. Frontend pages
print("\n--- 1. Frontend Pages ---")
pages = ["index","login","register","admin-login","admin","user","employee",
         "forgot-password","about","contact","faq","blog","help","privacy","terms","api-docs"]
for p in pages:
    try:
        req = urllib.request.Request(f"{FRONTEND}/{p}.html")
        resp = urllib.request.urlopen(req)
        check(f"{p}.html -> {resp.status}", resp.status == 200)
    except Exception as e:
        check(f"{p}.html -> ERROR: {e}", False)

# 2. Auth flow
print("\n--- 2. Auth Flow ---")
code, d = api("POST", "/api/auth/register", {"name":"AuditTest","email":"audit@test.com","phone":"+19000000001","password":"AuditPass1!"})
check(f"Register -> {code}", code in (201, 409))  # 409 = already exists (re-runs)
token = d.get("token", "")

# If register returned 409 (already exists), login to get a fresh token
if not token:
    code, d = api("POST", "/api/auth/login", {"email":"audit@test.com","password":"AuditPass1!"})
    token = d.get("token", "")

if not token:
    # Try resetting password via OTP to get access
    code, d = api("POST", "/api/auth/forgot-password", {"identifier":"audit@test.com"})
    otp = d.get("otp", "")
    code, d = api("POST", "/api/auth/verify-otp", {"identifier":"audit@test.com","otp":otp})
    reset_token = d.get("resetToken", "")
    api("POST", "/api/auth/reset-password", {"token":reset_token,"password":"AuditPass1!","confirmPassword":"AuditPass1!"})
    code, d = api("POST", "/api/auth/login", {"email":"audit@test.com","password":"AuditPass1!"})
    token = d.get("token", "")

code, d = api("POST", "/api/auth/login", {"email":"audit@test.com","password":"AuditPass1!"})
check(f"Login (email) -> {code}", code == 200 and "token" in d)
token = d.get("token", token)

code, d = api("POST", "/api/auth/login", {"email":"AuditTest","password":"AuditPass1!"})
check(f"Login (username) -> {code}", code == 200 and "token" in d)

code, d = api("POST", "/api/auth/login", {"email":"+19000000001","password":"AuditPass1!"})
check(f"Login (phone) -> {code}", code == 200 and "token" in d)

code, d = api("POST", "/api/auth/login", {"email":"audit@test.com","password":"wrong"})
check(f"Login (wrong pwd) -> {code} blocked", code == 401)

code, d = api("GET", "/api/auth/me", token=token)
check(f"GET /me (authed) -> {code}", code == 200 and d.get("name") == "AuditTest")

code, d = api("GET", "/api/auth/me")
check(f"GET /me (no auth) -> {code}", code == 401)

# 3. Forgot password
print("\n--- 3. Forgot Password ---")
code, d = api("POST", "/api/auth/forgot-password", {"identifier":"audit@test.com"})
check(f"Forgot password -> {code}", code == 200 and "otp" in d)
otp = d.get("otp", "")

code, d = api("POST", "/api/auth/verify-otp", {"identifier":"audit@test.com","otp":otp})
check(f"Verify OTP -> {code}", code == 200 and "resetToken" in d)
reset_token = d.get("reset_token", d.get("resetToken", ""))

code, d = api("POST", "/api/auth/reset-password", {"token":reset_token,"password":"NewPass123!","confirmPassword":"NewPass123!"})
check(f"Reset password -> {code}", code == 200)

code, d = api("POST", "/api/auth/login", {"email":"audit@test.com","password":"NewPass123!"})
check(f"Login (new pwd) -> {code}", code == 200 and "token" in d)

code, d = api("POST", "/api/auth/login", {"email":"audit@test.com","password":"AuditPass1!"})
check(f"Login (old pwd rejected) -> {code}", code == 401)

# 4. Admin/Employee auth
print("\n--- 4. Admin/Employee Auth ---")
code, d = api("POST", "/api/admin/login", {"user_id":"ADMIN-001","password":"admin123"})
check(f"Admin login -> {code}", code == 200 and "token" in d)

code, d = api("POST", "/api/admin/login", {"user_id":"EMP-001","password":"emp123"})
check(f"Employee login -> {code}", code == 200 and "token" in d)

# 5. API endpoints
print("\n--- 5. API Endpoints ---")
code, d = api("GET", "/api/constants")
check(f"GET /constants -> {code}", code == 200)

code, d = api("GET", "/api/gis")
check(f"GET /gis -> {code}", code == 200)

code, d = api("GET", "/api/community/leaderboard")
check(f"GET /leaderboard -> {code}", code == 200)

code, d = api("GET", "/api/community/initiatives")
check(f"GET /initiatives -> {code}", code == 200)

code, d = api("GET", "/api/reports", token=token)
check(f"GET /reports (authed) -> {code}", code == 200)

code, d = api("GET", "/api/reports")
check(f"GET /reports (no auth) -> {code}", code == 401)

code, d = api("POST", "/api/reports", {"wasteType":"Plastic","location":"Test Location","lat":28.6,"lng":77.2}, token=token)
check(f"POST /reports (create) -> {code}", code in (200, 201))

code, d = api("GET", "/health")
check(f"GET /health -> {code}", code == 200)

# Summary
print("\n" + "=" * 60)
print(f"RESULTS: {passed} passed, {failed} failed out of {passed + failed}")
print("=" * 60)
sys.exit(0 if failed == 0 else 1)
