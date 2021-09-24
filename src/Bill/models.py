from datetime import datetime
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import DECIMAL, DateTime, Float
from ..database import Base


class Billing(Base):
    __tablename__ = "billings"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    total = Column(Float, index=True)
    item_id = Column(Integer, ForeignKey("items.id"))
    category_id = Column(Integer, ForeignKey("categorys.id"))
    order_id = Column(Integer, ForeignKey("orders.id"))
