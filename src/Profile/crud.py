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


def create_profile(
    db: Session,
    img_name: str,
    img_url: str,
    first_name: str,
    last_name: str,
    address: str,
    user_id: str,
):
    db_img = models.UserProfile(
        img_name=img_name,
        img_url=img_url,
        first_name=first_name,
        last_name=last_name,
        address=address,
        user_id=user_id,
    )
    db.add(db_img)
    db.commit()
    db.refresh(db_img)
    return db_img


def profiles(db: Session, skip: int = 0, limit: int = 100):
    data = db.query(models.UserProfile).offset(skip).limit(limit).all()
    return data


def get_user_profile(db: Session, user_id: int):
    db_user = (
        db.query(
            models.UserProfile.first_name,
            models.UserProfile.last_name,
            models.UserProfile.img_name,
            models.UserProfile.img_url,
        )
        .filter(models.UserProfile.user_id == user_id)
        .all()
    )
    for userprofile in db_user:
        print(userprofile)

    return db_user


def delete_profile(db: Session, profile_id: int):
    delete_profile = (
        db.query(models.UserProfile).filter(models.UserProfile.id == profile_id).first()
    )
    db.delete(delete_profile)
    db.commit()
    return delete_profile


def update_profile(
    db: Session,
    img_name: str,
    img_url: str,
    first_name: str,
    last_name: str,
    address: str,
    user_id: str,
    profile_id: int,
):
    update_category = (
        db.query(models.UserProfile).filter(models.UserProfile.id == profile_id).first()
    )
    update_category.img_name = img_name
    update_category.img_url = img_url
    update_category.first_name = first_name
    update_category.last_name = last_name
    update_category.address = address
    update_category.user_id = user_id

    db.commit()
    db.refresh(update_category)
    return update_category
