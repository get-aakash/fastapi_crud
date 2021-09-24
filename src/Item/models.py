from datetime import datetime
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import DECIMAL, DateTime, Float
from ..database import Base


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    item_title = Column(String, index=True)
    item_price = Column(DECIMAL, index=True)
    item_description = Column(String, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    category_id = Column(Integer, ForeignKey("categorys.id"))

    owner = relationship("User", back_populates="items")
    category_list = relationship("Category", back_populates="items_list")
