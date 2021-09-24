from datetime import datetime
from src.Item.schemas import Item
from src.Category.schemas import Category


from typing import List, Optional

from pydantic.main import BaseModel


class UserBase(BaseModel):
    full_name: str
    email: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    is_staff: bool
    items: List[Item] = []
    category: List[Category] = []

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenDataBase(BaseModel):
    token_data: str
    counter: int


class TokenDataCreate(TokenDataBase):
    pass


class TokenData(TokenDataBase):
    id: int
    owner_id: int


class ResetPassword(BaseModel):
    old_password: str
    new_password: str
    confirm_password: str


class ForgotPassword(BaseModel):
    email: str


class ResetCode(BaseModel):
    reset_code: str
    expired_in: str
