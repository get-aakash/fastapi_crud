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


def create_cart(db: Session, user_id: int, category_id: int, item_id: int):
    db_cart = models.Cart(owner_id=user_id, category_id=category_id, item_id=item_id)
    db.add(db_cart)
    db.commit()
    db.refresh(db_cart)
    return db_cart


def get_carts(db: Session, user_id: int):
    return (
        db.query(
            models.Cart.id,
            models.Item.item_title,
            models.Item.item_description,
            models.Item.item_price,
        )
        .select_from(models.Cart)
        .join(models.Item)
        .filter(models.Cart.owner_id == user_id)
        .all()
    )


def get_cart(db: Session, item_id: int, user_id: int):
    return (
        db.query(models.Cart)
        .filter(models.Cart.item_id == item_id, models.Cart.owner_id == user_id)
        .first()
    )


def get_cart_by_id(db: Session, cart_id: int):
    return db.query(models.Cart).filter(models.Cart.id == cart_id).first()


def get_order_by_id(db: Session, order_id: int):
    return db.query(models.Order).filter(models.Order.id == order_id).first()


def get_cart_by_item(db: Session, item_id: int):
    return db.query(models.Cart).filter(models.Cart.item_id == item_id).first()


def delete_cart(db: Session, item_id: int):
    delete_cart = db.query(models.Cart).filter(models.Cart.item_id == item_id).first()
    db.delete(delete_cart)
    db.commit()
    return delete_cart
