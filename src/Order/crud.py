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


def get_order(db: Session, user_id: int):

    data = db.query(models.Order).filter(models.Order.owner_id == user_id).all()

    sample = []

    for dbs in data:

        value = (
            db.query(
                models.Order.id,
                models.Category.category_title,
                models.Item.item_title,
                models.Item.item_description,
                models.Item.item_price,
                models.Order.quantity,
                models.Order.address,
            )
            .select_from(models.Order)
            .join(models.Category)
            .filter(models.Order.id == dbs.id)
            .filter(models.Item.id == dbs.item_id)
            .all()
        )

        sample.append(value)

    return {"Items ordered": sample}


def get_orders(db: Session, user_id: int):
    return db.query(models.Order).filter(models.Order.owner_id == user_id).all()
