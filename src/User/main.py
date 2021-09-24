import os

from src.User.emails import forgot_password_email, send_email
from typing import List, Optional
from datetime import datetime, timedelta
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt
from fastapi.responses import HTMLResponse
from src.User import models, schemas, crud
from src.database import engine
from fastapi.templating import Jinja2Templates
from fastapi import APIRouter

import uuid
from src.User.dependencies import get_db, get_current_user


SECRET_KEY = "96ef2d27f39d6a6f4a919495b097b841051f30b0fad4aed2c30069671bc9c70a"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
models.Base.metadata.create_all(bind=engine)
router = APIRouter(prefix="/users")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@router.post("/create_user/", response_model=schemas.User, tags=["User"])
async def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
):
    """Demonstrates triple double quotes
    docstrings and does nothing really."""

    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = crud.create_user(db=db, user=user)
    await send_email([user.email], user, db=db)
    raise HTTPException(
        status_code=200,
        detail=f"New user with user name {user.full_name} !!! has been created!!",
    )


@router.post("/super_user/", response_model=schemas.User, tags=["User"])
async def create_super_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
):

    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = crud.create_super_user(db=db, user=user)
    await send_email([user.email], user, db=db)
    raise HTTPException(
        status_code=200,
        detail=f"New user with user name {user.full_name} !!! has been created!!",
    )


templates = Jinja2Templates(directory=os.path.abspath(os.path.expanduser("templates")))


@router.get("/verification", response_class=HTMLResponse, tags=["Authentication"])
async def email_verfication(request: Request, id: str, db: Session = Depends(get_db)):

    data = await crud.verify_token(id, db)

    if data.expired_in < datetime.now():
        raise HTTPException(status_code=401, detail="The code has already been expired")
    user = db.query(models.User).filter(models.User.id == data.owner_id).first()
    if user and not user.is_active:
        user.is_active = True
        db.add(user)
        db.commit()
        return templates.TemplateResponse(
            "verification.html",
            context={"request": request, "username": user.full_name},
        )
    if user and user.is_active:
        raise HTTPException(status_code=401, detail="Email already verified")
    else:
        raise HTTPException(status_code=401, detail="User does not exist")


@router.post("/login", tags=["Authentication"])
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user_value = crud.get_user_by_username(db, form_data.username)
    username = user_value.full_name
    password = user_value.hashed_password
    verify_password = crud.check_password(form_data.password, password)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username is incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not verify_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="password is incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"user": username}, expires_delta=access_token_expires
    )
    if not user_value.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email not verified",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=schemas.User, tags=["User"])
def view_user_profile(current_user: schemas.User = Depends(get_current_user)):
    return current_user


@router.get("/view_users/", response_model=List[schemas.User], tags=["User"])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):

    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=schemas.User, tags=["User"])
def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):

    db_user = crud.get_user(db=db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="user does not exist")
    return db_user


@router.delete("/{user_id}", tags=["User"])
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    db_delete = crud.delete_user(db=db, user_id=user_id)
    if db_delete is None:
        raise HTTPException(status_code=404, detail="User not deleted")
    return {"message": f"successfully deleted the user with id: {user_id}"}


@router.put("/{user_id}", response_model=schemas.User, tags=["User"])
def update_user(
    user_id: int,
    new_password: str,
    new_email: str,
    new_full_name: str,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    update_user = crud.update_user(
        db=db,
        user_id=user_id,
        new_password=new_password,
        new_email=new_email,
        new_full_name=new_full_name,
    )
    if update_user is None:
        raise HTTPException(status_code=404, detail="user not updated")
    return {"message": f"successfully updated the user with id: {user_id}"}


@router.patch("/reset_password", tags=["Authentication"])
async def password_reset(
    reset_password: schemas.ResetPassword,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username: str = payload.get("user")
    current_user = crud.get_user_by_username(db, username=username)
    password = current_user.hashed_password
    verify_password = crud.check_password(reset_password.old_password, password)
    if not verify_password:
        raise credentials_exception
    if reset_password.new_password != reset_password.confirm_password:
        raise HTTPException(
            status_code=404, detail="new password and confirm password doesnot match"
        )
    crud.check_reset_password(reset_password.new_password, current_user.id, db)

    return {
        "message": f"successfully updated the password for the user name: {current_user.full_name}"
    }


@router.post("/forgot-password", tags=["Authentication"])
async def forgot_password(
    request: schemas.ForgotPassword,
    db: Session = Depends(get_db),
):

    user = crud.get_user_by_email(db, request.email)
    if not user:
        raise HTTPException(status_code=404, detail="Email not registered")

    reset_code = str(uuid.uuid1())
    data = crud.get_reset_code(db, request.email)
    if data is None:
        await crud.forgot_password(request.email, reset_code, db)
        await forgot_password_email(reset_code, [request.email])

        return [{"message": "The reset code has been sent to your email"}]

    if data.email and data.expired_in > datetime.now():
        return [
            {"message": "The reset code is already sent. Please check your email!!"}
        ]
    if data.email and data.expired_in < datetime.now():
        reset_code = str(uuid.uuid1())
        data = crud.update_reset_code(db, request.email, reset_code)
        await forgot_password_email(reset_code, [request.email])
        return [
            {
                "message": "The existing code has expired.The new reset code has already been sent"
            }
        ]


@router.get("/new_password/{reset_code}", tags=["Authentication"])
async def request_new_password(
    reset_code: str,
    new_password: str,
    confirm_new_password: str,
    db: Session = Depends(get_db),
):
    data = crud.get_email_by_reset_code(db, reset_code)
    if not data:
        raise HTTPException(status_code=404, detail="Reset code does not exist")

    if data.expired_in < datetime.now():
        return [{"message": "The reset code has expired request a new one"}]
    if new_password != confirm_new_password:
        return [{"message": "new password and confirm password does not match!!"}]

    user = crud.get_user_by_email(db, data.email)
    crud.check_reset_password(new_password, user.id, db)
    return [{"message": "New password has been set please sign in to continue"}]
