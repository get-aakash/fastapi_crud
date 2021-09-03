from datetime import datetime
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
    item_title: str
    item_price: float
    item_description: Optional[str] = None


class ItemCreate(ItemBase):
    pass


class Item(ItemBase):
    id: int
    owner_id: int
    category_id: int

    class Config:
        orm_mode = True


class CartBase(BaseModel):
    pass


class CartCreate(CartBase):
    pass


class Cart(CartBase):
    id: int
    owner_id: int
    category_id: int
    item_id: int

    class Config:
        orm_mode = True


class CategoryBase(BaseModel):
    category_title: str
    category_description: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class Category(CategoryBase):
    id: int
    owner_id: int
    items_list: List[Item] = []

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
    is_admin: bool
    is_staff: bool
    items: List[Item] = []
    category: List[Category] = []

    class Config:
        orm_mode = True


class TokenData(BaseModel):
    username: Optional[str] = None


class ResetPassword(BaseModel):
    old_password: str
    new_password: str
    confirm_password: str


class ForgotPassword(BaseModel):
    email: str


class ResetCode(BaseModel):
    reset_code: str
    expired_in: str


class OrderBase(BaseModel):
    address: str
    quantity: int


class OrderCreate(OrderBase):
    pass


class Order(OrderBase):
    id: int
    cart_id: int
    owner_id: int
    item_id: int
    category_id: int
    order_id: int

    class Config:
        orm_mode = True


class BillBase(BaseModel):
    total: float


class BillCreate(BillBase):
    pass


class Bill(BillBase):
    id: int
    owner_id: int
    item_id: int
    category_id: int

    class Config:
        orm_mode = True


class UserProfileBase(BaseModel):
    first_name: str
    last_name: str
    address: str
    img_url: str
    img_name: str


class UserProfileCreate(UserProfileBase):
    pass


class UserProfile(UserProfileBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True
