from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from src import crud

from src.Cart.dependencies import oauth2_scheme, get_current_user, get_db
from fastapi import APIRouter


router = APIRouter(prefix="/carts")


@router.post("/cart/{item_id}/", tags=["Cart"])
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
            item_id=db_item[1],
            category_id=db_item[2],
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


@router.get("/cart", tags=["Cart"])
def view_cart(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    current_user = get_current_user(db=db, token=token)

    if current_user is None:
        raise HTTPException(status_code=404, detail="user does not exist")
    data = crud.get_carts(db=db, user_id=current_user.id)

    return data


@router.delete("/cart/{item_id}", tags=["Cart"])
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
