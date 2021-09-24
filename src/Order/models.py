from datetime import datetime
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import DECIMAL, DateTime, Float
from ..database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    address = Column(String, index=True)
    quantity = Column(Integer, index=True)
    cart_id = Column(Integer, ForeignKey("carts.id"))
    owner_id = Column(Integer, ForeignKey("users.id"))
    item_id = Column(Integer, ForeignKey("items.id"))
    category_id = Column(Integer, ForeignKey("categorys.id"))
