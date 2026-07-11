import re
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator

class LoginSchema(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class RecordSchema(BaseModel):
    record_id: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=120)
    age: int = Field(ge=1, le=120)
    sex: str = Field(min_length=1, max_length=20)
    fees: float = Field(gt=0)
    email: EmailStr
    phone: str
    address: str = Field(min_length=1, max_length=500)
    city: str = Field(min_length=1, max_length=100)
    state: str = Field(min_length=1, max_length=100)
    country: str = Field(min_length=1, max_length=100)
    occupation: str = Field(min_length=1, max_length=120)
    blood_group: Optional[str] = Field(default=None, max_length=10)
    nationality: str = Field(min_length=1, max_length=80)
    marital_status: Optional[str] = Field(default=None, max_length=30)
    aadhaar: str
    pan: str
    remarks: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("phone")
    @classmethod
    def phone_valid(cls, value):
        if not re.fullmatch(r"[6-9]\d{9}", value):
            raise ValueError("Phone number must be a valid 10 digit Indian mobile number")
        return value

    @field_validator("aadhaar")
    @classmethod
    def aadhaar_valid(cls, value):
        if not re.fullmatch(r"\d{12}", value):
            raise ValueError("Aadhaar must contain exactly 12 digits")
        return value

    @field_validator("pan")
    @classmethod
    def pan_valid(cls, value):
        value = value.upper()
        if not re.fullmatch(r"[A-Z]{5}[0-9]{4}[A-Z]", value):
            raise ValueError("PAN must match format ABCDE1234F")
        return value

class UserCreateSchema(BaseModel):
    full_name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: str
    @field_validator("role")
    @classmethod
    def role_valid(cls, value):
        value = value.upper()
        if value not in {"ADMIN", "CLIENT"}:
            raise ValueError("Role must be ADMIN or CLIENT")
        return value

class UserUpdateSchema(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    status: Optional[str] = None
    role: Optional[str] = None

class ActionSchema(BaseModel):
    id: int = Field(gt=0)

