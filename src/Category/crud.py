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


def create_category(category: schemas.CategoryCreate, db: Session, user_id: int):
    db_category = models.Category(**category.dict(), owner_id=user_id)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


def get_categorys(db: Session, skip: int = 0, limit: int = 100):
    data = db.query(models.Category).offset(skip).limit(limit).all()
    return data


def get_category(db: Session, category_id: int):
    data = db.query(models.Category).filter(models.Category.id == category_id).first()
    return data


def delete_category(db: Session, category_id: int):
    delete_category = (
        db.query(models.Category).filter(models.Category.id == category_id).first()
    )
    db.delete(delete_category)
    db.commit()
    return delete_category


def update_category(db: Session, category_id: int, category: schemas.CategoryCreate):
    update_category = (
        db.query(models.Category).filter(models.Category.id == category_id).first()
    )
    update_category.description = category.description
    update_category.title = category.title

    db.commit()
    db.refresh(update_category)
    return update_category
