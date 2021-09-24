from datetime import datetime
from typing import List, Optional

from pydantic.main import BaseModel


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
