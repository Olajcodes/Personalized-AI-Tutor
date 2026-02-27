"""Auth schemas (register/login)."""

from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Literal["student", "teacher", "admin"] = "student"


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class AuthOut(BaseModel):
    access_token: str
    user_id: str
    role: str


class RegisterOut(BaseModel):
    user_id: str
    email: EmailStr
    role: str
    message: str


class ChangePasswordIn(BaseModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class MessageOut(BaseModel):
    message: str
