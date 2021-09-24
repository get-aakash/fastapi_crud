from datetime import datetime
from typing import List, Optional

from pydantic.main import BaseModel


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
