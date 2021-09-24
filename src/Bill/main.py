from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from src import crud
from src.Bill.dependencies import get_db, get_current_user, oauth2_scheme

from email import *

from fastapi import APIRouter


router = APIRouter(prefix="/bills")


@router.post("/bill/{order_id}", tags=["Bill"])
def create_bill(
    order_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):

    current_user = get_current_user(db=db, token=token)
    db_bill = crud.get_bill(db=db, user_id=current_user.id, order_id=order_id)
    print(db_bill)

    db_order = crud.get_order_by_id(db=db, order_id=order_id)
    item_price = crud.get_item(db=db, item_id=db_order.item_id)

    if db_order.owner_id != current_user.id:
        return HTTPException(
            status_code=401,
            detail="The Order ID is not valid. Please Enter the correct One",
        )
    if db_bill:
        return {"message": f"The bill with bill id {db_bill.order_id} already exist!!"}
    data = crud.bill(
        db=db,
        owner_id=current_user.id,
        total=db_order.quantity * item_price[5],
        item_id=db_order.item_id,
        category_id=db_order.category_id,
        order_id=order_id,
    )

    return {"message": "Bill Created"}


@router.get("/bill/", tags=["Bill"])
async def get_bill(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    current_user = get_current_user(db=db, token=token)
    db_bill = crud.get_bills(db=db, user_id=current_user.id)
    if db_bill is None:
        return HTTPException(status_code=401, detail="Bill does not exist")
