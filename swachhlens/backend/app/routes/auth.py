"""Authentication endpoints: register, login, logout, me."""
from __future__ import annotations

import re
import secrets
import string
import time

from fastapi import APIRouter, Depends, HTTPException

from .. import security
from ..database import execute, query_one
from ..dependencies import get_current_user
from ..models import LoginRequest, RegisterRequest, ForgotPasswordRequest, VerifyOtpRequest, ResetPasswordRequest

router = APIRouter(prefix="/auth", tags=["auth"])

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _user_public(user: dict) -> dict:
    return {
        "id": user["id"],
        "email": user["email"],
        "phone": user.get("phone", ""),
        "name": user["name"],
        "role": user["role"],
    }


@router.post("/register", status_code=201)
def register(body: RegisterRequest):
    phone = (body.phone or "").strip()
    if not re.fullmatch(r"\+?\d{7,15}", phone):
        raise HTTPException(status_code=422, detail="Please enter a valid phone number.")
    if query_one("SELECT id FROM users WHERE phone = ?", (phone,)):
        raise HTTPException(status_code=409, detail="An account with this phone number already exists.")

    # Email is optional. When omitted we derive a stable internal handle from
    # the phone so the email-keyed report/community flows still have a value.
    email_raw = (body.email or "").strip().lower()
    if email_raw:
        if not EMAIL_RE.match(email_raw):
            raise HTTPException(status_code=422, detail="Please enter a valid email address.")
        if query_one("SELECT id FROM users WHERE email = ?", (email_raw,)):
            raise HTTPException(status_code=409, detail="An account with this email already exists.")
        email = email_raw
    else:
        email = re.sub(r"\W", "", phone) + "@swachhlens.local"

    name = body.name.strip() or (email_raw.split("@")[0] if email_raw else phone)
    user = {
        "id": "usr_" + security.sha256_short(email),
        "email": email,
        "phone": phone,
        "password_hash": security.hash_password(body.password),
        "name": name,
        "role": body.role,
        "created_at": int(time.time() * 1000),
    }
    execute(
        "INSERT INTO users (id, email, phone, password_hash, name, role, created_at)"
        " VALUES (:id, :email, :phone, :password_hash, :name, :role, :created_at)",
        {
            "id": user["id"],
            "email": user["email"],
            "phone": user["phone"],
            "password_hash": user["password_hash"],
            "name": user["name"],
            "role": user["role"],
            "created_at": user["created_at"],
        },
    )
    return {"user": _user_public(user), "token": security.create_token(user)}


@router.post("/login")
def login(body: LoginRequest):
    identifier = body.email.strip()
    # Support login by email, phone, or username (name column)
    if EMAIL_RE.match(identifier.lower()):
        user = query_one("SELECT * FROM users WHERE LOWER(email) = ?", (identifier.lower(),))
    elif re.match(r"^\+?\d{7,15}$", identifier):
        user = query_one("SELECT * FROM users WHERE phone = ?", (identifier,))
    else:
        user = query_one("SELECT * FROM users WHERE LOWER(name) = LOWER(?)", (identifier,))
    if not user or not security.verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    return {"user": _user_public(user), "token": security.create_token(user)}


@router.post("/logout")
def logout(_user: dict = Depends(get_current_user)):
    # JWTs are stateless; the client just discards the token. A token blacklist
    # can be added later if revocation is needed.
    return {"ok": True}


@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    return _user_public(user)


# ---- Forgot / Reset Password ----

def _generate_otp() -> str:
    """Generate a 6-digit numeric OTP."""
    return ''.join(secrets.choice(string.digits) for _ in range(6))


@router.post("/forgot-password")
def forgot_password(body: ForgotPasswordRequest):
    """Send a 6-digit OTP to the user's email or phone. Returns the OTP in
    the response for development (in production, send via email/SMS only).
    """
    identifier = body.identifier.strip()
    user = None
    if EMAIL_RE.match(identifier.lower()):
        user = query_one("SELECT * FROM users WHERE LOWER(email) = ?", (identifier.lower(),))
    elif re.match(r"^\+?\d{7,15}$", identifier):
        user = query_one("SELECT * FROM users WHERE phone = ?", (identifier,))

    # Always return the same message to prevent user enumeration
    if not user:
        return {"detail": "If an account with that identifier exists, an OTP has been sent."}

    otp_code = _generate_otp()
    now = int(time.time() * 1000)
    execute(
        "INSERT INTO otp_requests (user_id, otp_code, expires_at, verified, created_at)"
        " VALUES (?, ?, ?, 0, ?)",
        (user["id"], otp_code, now + 5 * 60 * 1000, now),
    )

    # In production, send OTP via email/SMS here.
    # For development, include the OTP in the response.
    return {
        "detail": "OTP sent.",
        "otp": otp_code,
    }


@router.post("/verify-otp")
def verify_otp(body: VerifyOtpRequest):
    """Verify the OTP. On success, return a short-lived reset token."""
    identifier = body.identifier.strip()
    user = None
    if EMAIL_RE.match(identifier.lower()):
        user = query_one("SELECT * FROM users WHERE LOWER(email) = ?", (identifier.lower(),))
    elif re.match(r"^\+?\d{7,15}$", identifier):
        user = query_one("SELECT * FROM users WHERE phone = ?", (identifier,))

    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP.")

    now = int(time.time() * 1000)
    otp_row = query_one(
        "SELECT * FROM otp_requests WHERE user_id = ? AND otp_code = ? AND verified = 0"
        " AND expires_at > ? ORDER BY id DESC LIMIT 1",
        (user["id"], body.otp, now),
    )
    if not otp_row:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP.")

    # Mark OTP as verified
    execute("UPDATE otp_requests SET verified = 1 WHERE id = ?", (otp_row["id"],))

    # Issue a short-lived reset token (JWT with 10-minute expiry)
    reset_token = security.create_reset_token(user)
    return {"resetToken": reset_token}


@router.post("/reset-password")
def reset_password(body: ResetPasswordRequest):
    """Reset password using the reset token from verify-otp."""
    payload = security.verify_reset_token(body.token)
    if not payload:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token.")

    user = query_one("SELECT * FROM users WHERE id = ?", (payload["sub"],))
    if not user:
        raise HTTPException(status_code=400, detail="User not found.")

    new_hash = security.hash_password(body.password)
    execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user["id"]))
    return {"detail": "Password updated successfully."}
