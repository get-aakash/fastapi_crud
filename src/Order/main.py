from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from src.Order import crud, schemas
from src.Order.dependencies import get_db, get_current_user, oauth2_scheme


from fastapi import APIRouter


router = APIRouter(prefix="/orders")


@router.post("/order/{cart_id}/", tags=["Order"])
def Order(
    cart_id: int,
    order: schemas.OrderCreate,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    current_user = get_current_user(db=db, token=token)
    data = crud.get_cart_by_id(cart_id=cart_id, db=db)
    if data is None:
        raise HTTPException(status_code=404, detail="cart not found")
    if current_user.id != data.owner_id:
        return HTTPException(
            status_code=401,
            detail="No item in the cart!! Please enter a valid cart ID!!",
        )

    db_order = crud.get_orders(db=db, user_id=current_user.id)
    for d in db_order:
        if d.cart_id == cart_id:
            return {"message": "The order is already placed"}
    if db_order is None:
        order = crud.order(
            db=db,
            user_id=current_user.id,
            cart_id=cart_id,
            order=order,
            category_id=data.category_id,
            item_id=data.item_id,
        )
        return {"message": f"successfully placed the order with id: {order.id}"}

    order = crud.order(
        db=db,
        user_id=current_user.id,
        cart_id=cart_id,
        order=order,
        category_id=data.category_id,
        item_id=data.item_id,
    )
    return {"message": f"successfully placed the order with id: {order.id}"}


@router.get("/order", tags=["Order"])
def get_order(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    current_user = get_current_user(db=db, token=token)
    order = crud.get_order(db=db, user_id=current_user.id)

    if order is None:
        raise HTTPException(status_code=404, detail="Order does not exist")

    return order
