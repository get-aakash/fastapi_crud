import os
import secrets
from fastapi.staticfiles import StaticFiles
from PIL import Image
from pydantic.errors import DateError
from pydantic.types import FilePath
from sqlalchemy.sql.functions import current_user
from starlette.responses import JSONResponse
from pydantic.schema import schema
from fastapi import BackgroundTasks, File, UploadFile
from emails import EmailSchema, forgot_password_email, send_email
from typing import List, Optional
from datetime import datetime, timedelta
from passlib.context import CryptContext
from fastapi import Depends, FastAPI, HTTPException, Request, status, Form
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from fastapi.responses import HTMLResponse
from src import models, schemas, crud
from src.database import SessionLocal, engine
from fastapi.templating import Jinja2Templates
from re import template
from email import *
import uuid
import emails


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


@app.post("/create_user/", response_model=schemas.User, tags=["User"])
async def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
):

    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = crud.create_user(db=db, user=user)
    await send_email([user.email], user, db=db)
    raise HTTPException(
        status_code=200,
        detail=f"New user with user name {user.full_name} !!! has been created!!",
    )


@app.post("/super_user/", response_model=schemas.User, tags=["User"])
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


@app.get("/verification", response_class=HTMLResponse, tags=["Authentication"])
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
    if not user_value.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email not verified",
            headers={"WWW-Authenticate": "Bearer"},
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

    if current_user is None:
        raise credentials_exception
    return current_user


@app.get("/user/me", response_model=schemas.User, tags=["User"])
def view_user_profile(current_user: schemas.User = Depends(get_current_user)):
    return current_user


@app.get("/view_users/", response_model=List[schemas.User], tags=["User"])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):

    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.get("/user/{user_id}", response_model=schemas.User, tags=["User"])
def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):

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
    return {"message": f"successfully updated the user with id: {user_id}"}


@app.post("/users/{user_id}", tags=["Item"])
def create_item(
    category_id: int,
    item: schemas.ItemCreate,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):

    current_user = get_current_user(db=db, token=token)
    if current_user is None:
        raise HTTPException(status_code=404, detail="user does not exist")
    if current_user.is_admin is False:
        raise HTTPException(status_code=401, detail="Only admins can create Item")
    category = crud.get_category(db=db, category_id=category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Category does not exist")
    datas = crud.create_item(
        db=db,
        user_id=current_user.id,
        item=item,
        category_id=category_id,
    )

    return {
        "message": f"successfully created the item with id: {datas.id} and title: {datas.item_title}"
    }


@app.get("/items", tags=["Item"])
def get_items(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    items = crud.get_items(db, skip=skip, limit=limit)
    db_category = crud.get_categorys(db=db, skip=skip, limit=limit)

    return items


@app.get("/item/{item_id}", tags=["Item"])
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
    current_user = get_current_user(db=db, token=token)
    if current_user is None:
        raise HTTPException(status_code=404, detail="user does not exist")
    if current_user.is_admin is False:
        raise HTTPException(status_code=401, detail="Only admins can delete Item")
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
    current_user = get_current_user(db=db, token=token)
    if current_user is None:
        raise HTTPException(status_code=404, detail="user does not exist")
    if current_user.is_admin is False:
        raise HTTPException(status_code=401, detail="Only admins can update Item")
    update_item = crud.update_item(db=db, item=item, item_id=item_id)
    if update_item is None:
        raise HTTPException(status_code=404, detail="Item not updated")
    return {"message": f"successfully updated the item with id: {item_id}"}


@app.patch("/reset_password", tags=["Authentication"])
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


@app.post("/forgot-password", tags=["Authentication"])
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


@app.get("/new_password/{reset_code}", tags=["Authentication"])
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


@app.post("/users/", tags=["Category"])
def create_category(
    item: schemas.CategoryCreate,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    current_user = get_current_user(db=db, token=token)
    if current_user is None:
        raise HTTPException(status_code=404, detail="user does not exist")
    if current_user.is_admin is False:
        raise HTTPException(status_code=404, detail="Only admins can create category")

    value = crud.create_category(db=db, user_id=current_user.id, category=item)

    return {
        "message": f"successfully created the category with id: {value.id} and title: {value.category_title}"
    }


@app.get("/categorys", response_model=List[schemas.Category], tags=["Category"])
def get_categorys(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    category = crud.get_categorys(db, skip=skip, limit=limit)

    return category


@app.get("/category/{category_id}", response_model=schemas.Category, tags=["Category"])
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    category = crud.get_category(db=db, category_id=category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="category does not exist")
    return category


@app.delete("/category/{category_id}", tags=["Category"])
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    current_user = get_current_user(db=db, token=token)
    if current_user is None:
        raise HTTPException(status_code=404, detail="user does not exist")
    if current_user.is_admin is False:
        raise HTTPException(status_code=401, detail="Only admins can delete category")
    delete_item = crud.delete_category(db=db, category_id=category_id)
    if delete_item is None:
        raise HTTPException(status_code=404, detail="Item not deleted")
    return {"message": f"successfully deleted the item with id: {category_id}"}


@app.put("/categorys/{category_id}", tags=["Category"])
def update_category(
    category_id: int,
    category: schemas.CategoryCreate,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    current_user = get_current_user(db=db, token=token)
    if current_user is None:
        raise HTTPException(status_code=404, detail="user does not exist")
    if current_user.is_admin is False:
        raise HTTPException(status_code=401, detail="Only admins can update category")
    update_item = crud.update_category(
        db=db, category=category, category_id=category_id
    )
    if update_item is None:
        raise HTTPException(status_code=404, detail="Category not updated")
    return {"message": f"successfully updated the category with id: {category_id}"}


@app.post("/cart/{item_id}/", tags=["Cart"])
def add_to_cart(
    item_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):

    current_user = get_current_user(db=db, token=token)
    db_cart = crud.get_cart(db, user_id=current_user.id, item_id=item_id)
    db_item = crud.get_item(db=db, item_id=item_id)
    if db_cart is None:
        cart = crud.create_cart(
            db=db,
            user_id=current_user.id,
            category_id=db_item[1],
            item_id=item_id,
        )
        return {"message": "Item added to the cart"}

    if db_cart.item_id & db_cart.owner_id == item_id & current_user.id:
        raise HTTPException(status_code=401, detail="The item is already on the cart")

    if db_item is None:
        raise HTTPException(status_code=404, detail="category does not exist")
    print(db_item[0])

    cart = crud.create_cart(
        db=db,
        user_id=current_user.id,
        category_id=db_item[1],
        item_id=item_id,
    )
    return {"message": f"successfully created the cart with id: {cart.id}"}


@app.get("/cart", tags=["Cart"])
def view_cart(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    current_user = get_current_user(db=db, token=token)

    if current_user is None:
        raise HTTPException(status_code=404, detail="user does not exist")
    data = crud.get_carts(db=db, user_id=current_user.id)
    return data


@app.delete("/cart/{item_id}", tags=["Cart"])
def delete_cart(
    item_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    current_user = get_current_user(db=db, token=token)

    db_cart = crud.get_carts(db, user_id=current_user.id)
    for dbs in db_cart:
        if dbs.item_id == item_id:
            crud.delete_cart(db=db, item_id=item_id)
            raise HTTPException(
                status_code=401, detail="The item in the cart  is  deleted"
            )

    raise HTTPException(status_code=404, detail="Cart not deleted or empty cart")


@app.post("/order/{cart_id}/", tags=["Order"])
def Order(
    cart_id: int,
    order: schemas.OrderCreate,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    current_user = get_current_user(db=db, token=token)
    data = crud.get_cart_by_id(cart_id=cart_id, db=db)
    if current_user.id != data.owner_id:
        return HTTPException(
            status_code=401,
            detail="No item in the cart!! Please enter a valid cart ID!!",
        )

    if data is None:
        raise HTTPException(status_code=401, detail="the cart does not exist")

    order = crud.order(
        db=db,
        user_id=current_user.id,
        cart_id=cart_id,
        order=order,
        category_id=data.category_id,
        item_id=data.item_id,
    )
    return {"message": f"successfully placed the order with id: {order.id}"}


@app.get("/order/{order_id}", tags=["Order"])
def get_order(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    current_user = get_current_user(db=db, token=token)
    order = crud.get_order(db=db, user_id=current_user.id)
    print(order)
    if order is None:
        raise HTTPException(status_code=404, detail="Order does not exist")
    return order


@app.post("/bill/", tags=["Bill"])
def create_bill(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):

    current_user = get_current_user(db=db, token=token)
    db_bill = crud.get_bill(db=db, owner_id=current_user.id)

    bill = 0
    order = crud.get_order(db=db, user_id=current_user.id)
    print(order)
    for value in order:
        item = crud.get_cart_by_id(db=db, cart_id=value[5])
        print(item)
        item_price = crud.get_item(db=db, item_id=item.item_id)
        print(item_price[5])
        total = value.quantity * item_price[5]
        bill = bill + total
    data = crud.bill(
        db=db,
        owner_id=current_user.id,
        total=bill,
        item_id=item.item_id,
        category_id=item.category_id,
    )
    return data


@app.get("/bill/{bill_id}", tags=["Bill"])
def get_bill(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    current_user = get_current_user(db=db, token=token)
    db_bill = crud.get_bill(db=db, owner_id=current_user.id)
    if db_bill is None:
        return HTTPException(status_code=401, detail="Bill does not exist")
    return db_bill


@app.get("/send-email/asynchronous")
async def send_email_asynchronous():
    await emails.send_email_async(
        "Hello World",
        "mail.aakash108@gmail.com",
        {"title": "Hello World", "name": "John Doe"},
    )
    return "Success"


@app.get("/form", response_class=HTMLResponse)
def form_return(request: Request):
    return templates.TemplateResponse(
        "form.html", context={"request": request, "username": "hello"}
    )


@app.post("/create_profile/", tags=["User Profile"])
async def create_profile(
    first_name: str = Form(...),
    last_name: str = Form(...),
    address: str = Form(...),
    assign_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):

    current_user = get_current_user(db=db, token=token)
    user = crud.get_user_profile(db=db, user_id=current_user.id)
    if user:
        return user
    if current_user is None:
        raise HTTPException(status_code=404, detail="user does not exist")
    FILEPATH = "./static/images/"
    filename = assign_file.filename
    extension = filename.split(".")[1]

    if extension not in ["png", "jpeg", "jpg"]:
        raise HTTPException(status_code=401, detail="extension does not match")
    token_name = filename
    generated_name = FILEPATH + token_name

    file_content = await assign_file.read()

    with open(generated_name, "wb") as file:
        file.write(file_content)

    img = Image.open(generated_name)
    img = img.resize(size=(200, 200))
    img.save(generated_name)
    file.close()

    file_url = generated_name[1:]
    value = crud.create_profile(
        img_name=token_name,
        db=db,
        img_url=file_url,
        first_name=first_name,
        last_name=last_name,
        address=address,
        user_id=current_user.id,
    )
    if value:
        return {"status": "ok", "file_url": file_url}


@app.get("/user_profile/", tags=["User Profile"])
def get_profile(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    current_user = get_current_user(db=db, token=token)
    db_user_profile = crud.get_user_profile(db=db, user_id=current_user.id)
    if db_user_profile is None:
        return HTTPException(status_code=401, detail="Bill does not exist")
    return db_user_profile


@app.get(
    "/get_all_profiles/",
    response_model=List[schemas.UserProfile],
    tags=["User Profile"],
)
def get_all_profiles(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    current_user = get_current_user(db=db, token=token)
    if current_user.is_admin:
        profile = crud.profiles(db, skip=skip, limit=limit)
        return profile
    else:
        raise HTTPException(status_code=401, detail="only super user can access")


@app.delete("/UserProfile/{profile_id}", tags=["User Profile"])
def delete_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    current_user = get_current_user(db=db, token=token)
    if current_user.is_admin:
        db_profile = crud.delete_profile(db=db, profile_id=profile_id)
        return db_profile
    else:
        raise HTTPException(status_code=401, detail="Only super user can delete")


@app.put("/profile/{profile_id}", tags=["User Profile"])
async def update_profile(
    profile_id: int,
    first_name: str = Form(...),
    last_name: str = Form(...),
    address: str = Form(...),
    assign_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    current_user = get_current_user(db=db, token=token)

    if current_user is None:
        raise HTTPException(status_code=404, detail="user does not exist")
    db_profile = crud.get_user_profile(db=db, user_id=current_user.id)
    if db_profile.user_id != profile_id:
        return HTTPException(status_code=401, detail="cannot update other user profile")

    FILEPATH = "./static/images/"
    filename = assign_file.filename
    extension = filename.split(".")[1]

    if extension not in ["png", "jpeg", "jpg"]:
        raise HTTPException(status_code=401, detail="extension does not match")
    token_name = filename
    generated_name = FILEPATH + token_name

    file_content = await assign_file.read()

    with open(generated_name, "wb") as file:
        file.write(file_content)

    img = Image.open(generated_name)
    img = img.resize(size=(200, 200))
    img.save(generated_name)
    file.close()

    file_url = generated_name[1:]
    update_profile = crud.update_profile(
        img_name=token_name,
        db=db,
        img_url=file_url,
        first_name=first_name,
        last_name=last_name,
        address=address,
        user_id=current_user.id,
        profile_id=profile_id,
    )
    if update_profile is None:
        raise HTTPException(status_code=404, detail="Category not updated")
    return {"message": f"successfully updated the profile with id: {profile_id}"}
