from datetime import datetime
from typing import List, Optional

from pydantic.main import BaseModel


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
