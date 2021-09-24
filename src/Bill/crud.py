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


def bill(
    db: Session,
    owner_id: int,
    total: float,
    category_id: int,
    item_id: int,
    order_id: int,
):
    db_bill = models.Billing(
        total=total,
        owner_id=owner_id,
        category_id=category_id,
        item_id=item_id,
        order_id=order_id,
    )
    db.add(db_bill)
    db.commit()
    db.refresh(db_bill)
    return db_bill


def get_bills(db: Session, user_id: int):
    bills = 0
    sample1 = []
    sample = []
    bill = db.query(models.Billing).filter(models.Billing.owner_id == user_id).all()
    for b in bill:
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
            .filter(models.Order.id == b.id)
            .filter(models.Item.id == b.item_id)
            .all()
        )
        print(b.total)
        bills = bills + b.total

        sample1.append(value)
    sample.append(bills)

    return {"Items Purchased": sample1, "Total": f"Rs.{sample}"}


def get_bill(db: Session, user_id: int, order_id: int):
    return (
        db.query(models.Billing)
        .filter(models.Billing.owner_id == user_id)
        .filter(models.Billing.order_id == order_id)
        .first()
    )


def get_bill_By_order_id(db: Session, user_id: int, order_id: int):
    return db.query(models.Billing).filter(models)
