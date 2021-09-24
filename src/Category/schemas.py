from datetime import datetime
from typing import List, Optional

from pydantic.main import BaseModel
from src.Item.schemas import Item


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
