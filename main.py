from pydantic.errors import DateError
from fastapi import Depends, FastAPI, HTTPException, Request, status, Form
from src.database import SessionLocal, engine
from src.User import models
from src.Bill import models
from src.Cart import models
from src.Category import models
from src.Item import models
from src.Order import models
from src.Profile import models
from src.User import main as user_main
from src.Bill import main as bill_main
from src.Cart import main as cart_main
from src.Category import main as category_main
from src.Item import main as item_main
from src.Order import main as order_main
from src.Profile import main as profile_main

models.Base.metadata.create_all(bind=engine)
models.Base.metadata.create_all(bind=engine)
models.Base.metadata.create_all(bind=engine)
models.Base.metadata.create_all(bind=engine)
models.Base.metadata.create_all(bind=engine)
models.Base.metadata.create_all(bind=engine)
models.Base.metadata.create_all(bind=engine)


app = FastAPI()


app.include_router(user_main.router)
app.include_router(bill_main.router)
app.include_router(cart_main.router)
app.include_router(order_main.router)
app.include_router(profile_main.router)
app.include_router(category_main.router)
app.include_router(item_main.router)
