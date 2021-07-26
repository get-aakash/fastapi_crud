from typing import List, Optional

from pydantic.main import BaseModel


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


class ItemBase(BaseModel):
    title: str
    description: Optional[str] = None


class ItemCreate(ItemBase):
    pass


class Item(ItemBase):
    id: int
    owner_id: int

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    full_name: str
    email: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    is_active: bool
    items: List[Item] = []

    class Config:
        orm_mode = True


class TokenData(BaseModel):
    username: Optional[str] = None


class ResetPassword(BaseModel):
    old_password: str
    new_password: str
    confirm_password: str
