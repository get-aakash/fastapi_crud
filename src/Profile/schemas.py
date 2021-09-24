from datetime import datetime
from typing import List, Optional

from pydantic.main import BaseModel


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
