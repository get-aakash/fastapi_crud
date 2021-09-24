from datetime import datetime
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import DECIMAL, DateTime, Float
from ..database import Base


class UserProfile(Base):
    __tablename__ = "userprofiles"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, index=True)
    last_name = Column(String, index=True)
    address = Column(String, index=True)
    img_url = Column(String, index=True)
    img_name = Column(String, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
