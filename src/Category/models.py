from datetime import datetime
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import DECIMAL, DateTime, Float
from ..database import Base


class Category(Base):
    __tablename__ = "categorys"

    id = Column(Integer, primary_key=True, index=True)
    category_title = Column(String, index=True)
    category_description = Column(String, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="category")
    items_list = relationship("Item", back_populates="category_list")
