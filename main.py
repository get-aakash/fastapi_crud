from emails import send_email
from typing import List
from passlib.context import CryptContext
from fastapi import Depends, FastAPI, HTTPException, Request
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from fastapi.responses import HTMLResponse
from src import models, schemas, crud
from src.database import SessionLocal, engine
from fastapi.templating import Jinja2Templates
from re import template
from email import *


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


@app.post("/users/", response_model=schemas.User, tags=["User"])
async def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    print("this is the create user")
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = crud.create_user(db=db, user=user)
    await send_email([user.email], models.User)


templates = Jinja2Templates(directory="templates")


@app.get("/verification", response_class=HTMLResponse)
async def email_verfication(request: Request, token: str):
    user = await crud.verify_token(token)
    if user and not user.is_verifed:
        user.is_active = True
        await user.save()
        return templates.TemplateResponse(
            "verification.html", {"request": request, "username": user.full_name}
        )
    raise HTTPException(status_code=401, details="unauthorised")


@app.get("/login", response_model=schemas.Token, tags=["User"])
def login_user(form_data: OAuth2PasswordRequestForm = Depends()):
    return {"access_token": form_data.username, "token_type": "bearer"}


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
def read_user(user_id: int, db: Session = Depends(get_db)):
    print("this is the read user")
    db_user = crud.get_user(db=db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="user does not exist")
    return db_user


@app.delete("/users/{user_id}", tags=["User"])
def delete_user(user_id: int, db: Session = Depends(get_db)):
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
def create_item(user_id: int, item: schemas.ItemCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user(db=db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="user does not exist")
    return crud.create_item(db=db, user_id=user_id, item=item)


@app.get("/items", response_model=List[schemas.Item], tags=["Item"])
def get_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    items = crud.get_items(db, skip=skip, limit=limit)
    return items


@app.get("/item/{item_id}", response_model=schemas.Item, tags=["Item"])
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = crud.get_item(db=db, item_id=item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="theres no item")
    return item


@app.delete("/item/{item_id}", tags=["Item"])
def delete_item(item_id: int, db: Session = Depends(get_db)):
    delete_item = crud.delete_item(db=db, item_id=item_id)
    if delete_item is None:
        raise HTTPException(status_code=404, detail="Item not deleted")
    return {"message": f"successfully deleted the item with id: {item_id}"}


@app.put("/items/{item_id}", tags=["Item"])
def update_item(item_id: int, item: schemas.ItemCreate, db: Session = Depends(get_db)):
    update_item = crud.update_item(db=db, item=item, item_id=item_id)
    if update_item is None:
        raise HTTPException(status_code=404, detail="Item not updated")
    return {"message": f"successfully updated the item with id: {item_id}"}
