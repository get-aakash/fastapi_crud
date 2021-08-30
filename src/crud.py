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


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
config_credentials = dotenv_values(".env")


def get_password_hash(password):
    return pwd_context.hash(password)


def check_password(password, hash_password) -> str:
    return pwd_context.verify(password, hash_password)


async def verify_token(id: str, db: Session):

    user = db.query(models.Token).filter(models.Token.token_data == id).first()

    return user


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_email_by_reset_code(db: Session, reset_code: str):
    return (
        db.query(models.ResetCode)
        .filter(models.ResetCode.reset_code == reset_code)
        .first()
    )


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_username(db, username: str):
    return db.query(models.User).filter(models.User.full_name == username).first()


def create_super_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        is_admin=True,
        is_staff=False,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
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


def pass_user(db: Session, username):
    user_value = db.query(models.User).filter(models.User.full_name == username).first()
    user_dict = jsonable_encoder(user_value)
    current_user = schemas.User(**user_dict)
    return current_user


def check_reset_password(new_password: str, id: int, db: Session):

    hashed_password = get_password_hash(new_password)
    db_user_to_update = db.query(models.User).filter(models.User.id == id).first()
    db_user_to_update.hashed_password = hashed_password
    db.add(db_user_to_update)
    db.commit()
    db.refresh(db_user_to_update)
    return db_user_to_update


async def forgot_password(email: str, reset_code: str, db: Session):
    data = db.query(models.ResetCode).filter(models.ResetCode.email == email).first()
    if data:
        return [{"message": "the reset code already exist"}]

    db_code = models.ResetCode(
        email=email,
        reset_code=reset_code,
        expired_in=datetime.now() + timedelta(minutes=15),
    )
    db.add(db_code)
    db.commit()
    db.refresh(db_code)
    return db_code


def update_reset_code(db: Session, email: str, reset_code: str):
    update_code = (
        db.query(models.ResetCode).filter(models.ResetCode.email == email).first()
    )
    update_code.email = email
    update_code.reset_code = reset_code
    update_code.expired_in = datetime.now() + timedelta(minutes=15)
    db.add(update_code)
    db.commit()
    db.refresh(update_code)
    return update_code


def get_reset_code(db: Session, email: str):
    return db.query(models.ResetCode).filter(models.ResetCode.email == email).first()


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
            models.User.full_name,
            models.Category.category_title,
            models.Item.item_title,
            models.Item.item_description,
            models.Item.item_price,
        )
        .select_from(models.Cart)
        .join(models.Category)
        .join(models.Item)
        .join(models.User)
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


def order(
    db: Session,
    user_id: int,
    cart_id: int,
    category_id: int,
    item_id: int,
    order: schemas.OrderCreate,
):
    db_order = models.Order(
        **order.dict(),
        cart_id=cart_id,
        owner_id=user_id,
        category_id=category_id,
        item_id=item_id,
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order


def get_order(db: Session, user_id: int):
    data = db.query(models.Order).filter(models.Order.owner_id == user_id).all()
    sample = []

    for dbs in data:

        value = (
            db.query(
                models.Category.category_title,
                models.Item.item_title,
                models.Item.item_description,
                models.Item.item_price,
            )
            .join(models.Category)
            .filter(models.Item.id == dbs.item_id)
            .all()
        )

        # sample.append([dbs.id, value, dbs.address, dbs.quantity])
        sample.append(dbs.id)
        sample.append(value)

        sample.append(dbs.address)

    return sample


def get_orders(db: Session, user_id: int):
    return db.query(models.Order).filter(models.Order.owner_id == user_id).first()


def bill(db: Session, owner_id: int, total: float, category_id: int, item_id: int):
    db_bill = models.Billing(
        total=total, owner_id=owner_id, category_id=category_id, item_id=item_id
    )
    db.add(db_bill)
    db.commit()
    db.refresh(db_bill)
    return db_bill


def get_bill(db: Session, owner_id: int):
    bill = (
        db.query(
            models.Billing.id,
            models.User.full_name,
            models.Order.address,
            models.Category.category_title,
            models.Item.item_title,
            models.Item.item_price,
            models.Order.quantity,
            models.Billing.total,
        )
        .filter(models.Item.id == models.Billing.item_id)
        .filter(models.Category.id == models.Billing.category_id)
        .filter(models.Billing.owner_id == owner_id)
        .first()
    )
    return bill


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
