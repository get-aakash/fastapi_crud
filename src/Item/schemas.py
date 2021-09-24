from datetime import datetime
from typing import List, Optional

from pydantic.main import BaseModel


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
