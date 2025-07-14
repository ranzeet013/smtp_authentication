# from pydantic import BaseModel, EmailStr

# class UserCreate(BaseModel):
#     name: str
#     email: EmailStr
#     password: str

# class UserLogin(BaseModel):
#     email: EmailStr
#     password: str

# class Token(BaseModel):
#     access_token: str
#     token_type: str

# class UserOut(BaseModel):
#     uuid: str
#     name: str
#     email: EmailStr
#     is_verified: bool

#     class Config:
#         orm_mode = True

# class ChangePassword(BaseModel):
#     current_password: str
#     new_password: str

# class OTPVerify(BaseModel):
#     email: EmailStr
#     otp: str

from pydantic import BaseModel, EmailStr
from typing import TypeVar, Generic, Optional

T = TypeVar("T")

class APIResponse(BaseModel, Generic[T]):
    status: str
    data: Optional[T]

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserOut(BaseModel):
    uuid: str
    name: str
    email: EmailStr
    is_verified: bool

    class Config:
        orm_mode = True

class ChangePassword(BaseModel):
    current_password: str
    new_password: str

class OTPVerify(BaseModel):
    email: EmailStr
    otp: str