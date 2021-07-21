from emails import send_email
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from . import models, schemas
import jwt
from dotenv import dotenv_values
from fastapi import status


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
config_credentials = dotenv_values(".env")


def get_password_hash(password):
    return pwd_context.hash(password)


async def verify_token(token: str):
    try:
        payload = jwt.decode(token, config_credentials["SECRET"])
        user = await models.User.get(id=payload.get("id"))

    except:
        raise HTTPException(status_code=404, detail="Invalid username or password")
    return user


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email, hashed_password=hashed_password, full_name=user.full_name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int):
    delete_user = db.query(models.User).filter(models.User.id == user_id).first()
    db.delete(delete_user)
    db.commit()
    return delete_user


def update_user(
    db: Session, user_id: int, new_password: str, new_email: str, new_full_name: str
):
    update_user = db.query(models.User).filter(models.User.id == user_id).first()
    update_user.hashed_password = new_password
    update_user.email = new_email
    update_user.full_name = new_full_name
    db.add(update_user)
    db.commit()
    db.refresh(update_user)
    return update_user


def create_item(item: schemas.ItemCreate, db: Session, user_id: int):
    db_item = models.Item(**item.dict(), owner_id=user_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def get_items(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Item).offset(skip).limit(limit).all()


def get_item(db: Session, item_id: int):
    return db.query(models.Item).filter(models.Item.id == item_id).first()


def delete_item(db: Session, item_id: int):
    delete_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    db.delete(delete_item)
    db.commit()
    return delete_item


def update_item(db: Session, item_id: int, item: schemas.ItemCreate):
    update_items = db.query(models.Item).filter(models.Item.id == item_id).first()
    update_items.description = item.description
    update_items.title = item.title

    db.commit()
    db.refresh(update_items)
    return update_items
