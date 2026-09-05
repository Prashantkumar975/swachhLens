"""Pydantic request/response models."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    # Phone is the required identifier; email is optional. When email is
    # blank the backend derives an internal handle from the phone number
    # (e.g. 9198…@swachhlens.local) so every email-keyed flow keeps working.
    phone: str = Field(min_length=1, max_length=20)
    email: Optional[str] = Field(default=None, max_length=200)
    password: str = Field(min_length=6, max_length=200)
    name: str = Field(default="", max_length=200)
    role: Literal["USER", "EMPLOYEE"] = "USER"


class LoginRequest(BaseModel):
    email: str = Field(description="Email or username")
    password: str


class ReportCreate(BaseModel):
    wasteType: str = Field(min_length=1, max_length=50)
    location: str = Field(min_length=1, max_length=300)
    lat: Optional[float] = None
    lng: Optional[float] = None
    desc: str = Field(default="", max_length=400)
    severity: Literal["Low", "Medium", "High"] = "Medium"
    photo: str = Field(default="", max_length=4_000_000)
    isBooking: bool = False
    scheduledAt: Optional[int] = None


class AssignRequest(BaseModel):
    groupId: Optional[str] = None
    memberId: Optional[str] = None


class ReassignRequest(BaseModel):
    memberId: str


class VerifyRequest(BaseModel):
    action: Literal["pass", "reject"] = "pass"


class AnalyzeRequest(BaseModel):
    photo: str = Field(min_length=16, max_length=4_000_000)


class BinUpdate(BaseModel):
    fill: int = Field(ge=0, le=100)


class AdminLoginRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=200)


class AdminTaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)
    assignedTo: Optional[str] = None


class AdminTaskAssign(BaseModel):
    assignedTo: str = Field(min_length=1, max_length=50)


class ForgotPasswordRequest(BaseModel):
    identifier: str = Field(min_length=1, max_length=200, description="Email or phone")


class VerifyOtpRequest(BaseModel):
    identifier: str = Field(min_length=1, max_length=200)
    otp: str = Field(min_length=6, max_length=6)


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=1, max_length=500)
    password: str = Field(min_length=8, max_length=200)
