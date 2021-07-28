from datetime import datetime
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import DateTime
from .database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=False)
    items = relationship("Item", back_populates="owner")


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    category_id = Column(Integer, ForeignKey("categorys.id"))

    owner = relationship("User", back_populates="items")


class Category(Base):
    __tablename__ = "categorys"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))


class Token(Base):
    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True, index=True)
    token_data = Column(String, index=True)
    expired_in = Column(DateTime, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))


class ResetCode(Base):
    __tablename__ = "reset_code"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    reset_code = Column(String, unique=True, index=True)
    expired_in = Column(DateTime, index=True)
