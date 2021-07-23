import os
from emails import send_email
from typing import List, Optional
from datetime import datetime, timedelta
from passlib.context import CryptContext
from fastapi import Depends, FastAPI, HTTPException, Request, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from fastapi.responses import HTMLResponse
from src import models, schemas, crud
from src.database import SessionLocal, engine
from fastapi.templating import Jinja2Templates
from re import template
from email import *


SECRET_KEY = "96ef2d27f39d6a6f4a919495b097b841051f30b0fad4aed2c30069671bc9c70a"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
models.Base.metadata.create_all(bind=engine)
app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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


@app.post("/users/", response_model=schemas.User, tags=["User"])
async def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):

    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = crud.create_user(db=db, user=user)
    await send_email([user.email], user)
    return user


templates = Jinja2Templates(directory=os.path.abspath(os.path.expanduser("templates")))


@app.get("/verification", response_class=HTMLResponse, tags=["Authentication"])
async def email_verfication(request: Request, id: int, db: Session = Depends(get_db)):
    print(email_verfication)
    user = await crud.verify_token(id, db)
    print(user)
    if user and not user.is_active:
        user.is_active = True
        db.add(user)
        db.commit()
        return templates.TemplateResponse(
            "verification.html",
            context={"request": request, "username": user.full_name},
        )

    raise HTTPException(status_code=401, detail="Email already verified")


@app.post("/login", tags=["Authentication"])
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
    return {"access_token": access_token, "token_type": "bearer"}


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("user")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception
    current_user = crud.pass_user(db, username=token_data.username)
    print(current_user)
    if current_user is None:
        raise credentials_exception
    return current_user


@app.get("/user/me", response_model=schemas.User, tags=["User"])
def view_user_profile(current_user: schemas.User = Depends(get_current_user)):
    return current_user


@app.get("/users/", response_model=List[schemas.User], tags=["User"])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):

    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.get("/user/{user_id}", response_model=schemas.User, tags=["User"])
def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    print("this is the read user")
    db_user = crud.get_user(db=db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="user does not exist")
    return db_user


@app.delete("/users/{user_id}", tags=["User"])
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    db_delete = crud.delete_user(db=db, user_id=user_id)
    if db_delete is None:
        raise HTTPException(status_code=404, detail="User not deleted")
    return {"message": f"successfully deleted the user with id: {user_id}"}


@app.put("/update_user/{user_id}", response_model=schemas.User, tags=["User"])
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
    return update_user


@app.post("/users/{user_id}/posts", response_model=schemas.Item, tags=["Item"])
def create_item(
    user_id: int,
    item: schemas.ItemCreate,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    db_user = crud.get_user(db=db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="user does not exist")
    return crud.create_item(db=db, user_id=user_id, item=item)


@app.get("/items", response_model=List[schemas.Item], tags=["Item"])
def get_items(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    items = crud.get_items(db, skip=skip, limit=limit)
    return items


@app.get("/item/{item_id}", response_model=schemas.Item, tags=["Item"])
def get_item(
    item_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    item = crud.get_item(db=db, item_id=item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="theres no item")
    return item


@app.delete("/item/{item_id}", tags=["Item"])
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    delete_item = crud.delete_item(db=db, item_id=item_id)
    if delete_item is None:
        raise HTTPException(status_code=404, detail="Item not deleted")
    return {"message": f"successfully deleted the item with id: {item_id}"}


@app.put("/items/{item_id}", tags=["Item"])
def update_item(
    item_id: int,
    item: schemas.ItemCreate,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    update_item = crud.update_item(db=db, item=item, item_id=item_id)
    if update_item is None:
        raise HTTPException(status_code=404, detail="Item not updated")
    return {"message": f"successfully updated the item with id: {item_id}"}
