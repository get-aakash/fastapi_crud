from datetime import datetime, timedelta

from fastapi.exceptions import HTTPException
from fastapi.param_functions import File
from sqlalchemy.orm import Session, session
from passlib.context import CryptContext
from . import models, schemas
import jwt
from dotenv import dotenv_values
from fastapi import status
from fastapi.encoders import jsonable_encoder


def create_item(
    item: schemas.ItemCreate,
    db: Session,
    user_id: int,
    category_id: int,
):
    db_item = models.Item(
        **item.dict(),
        owner_id=user_id,
        category_id=category_id,
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def get_items(db: Session, skip: int = 0, limit: int = 100):

    return db.query(models.Item).offset(skip).limit(limit).all()


def get_item(db: Session, item_id: int):
    db_item = (
        db.query(
            models.Category.category_title,
            models.Item.id,
            models.Category.id,
            models.Item.item_title,
            models.Item.item_description,
            models.Item.item_price,
        )
        .join(models.Category)
        .filter(models.Item.id == item_id)
        .first()
    )
    return db_item


def delete_item(db: Session, item_id: int):
    delete_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    db.delete(delete_item)
    db.commit()
    return delete_item


def update_item(db: Session, item_id: int, item: schemas.ItemCreate):
    update_items = db.query(models.Item).filter(models.Item.id == item_id).first()
    update_items.description = item.description
    update_items.title = item.title
    update_items.price = item.price

    db.commit()
    db.refresh(update_items)
    return update_items
