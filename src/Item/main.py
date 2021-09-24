from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from src.Item import schemas, crud
from src.Item.dependencies import oauth2_scheme, get_current_user, get_db
from fastapi import APIRouter


router = APIRouter(prefix="/items")


@router.post("/users/{user_id}", tags=["Item"])
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


@router.get("/items", tags=["Item"])
def get_items(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    items = crud.get_items(db, skip=skip, limit=limit)
    db_category = crud.get_categorys(db=db, skip=skip, limit=limit)

    return items


@router.get("/item/{item_id}", tags=["Item"])
def get_item(
    item_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    item = crud.get_item(db=db, item_id=item_id)

    if item is None:
        raise HTTPException(status_code=404, detail="theres no item")
    return item


@router.delete("/item/{item_id}", tags=["Item"])
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


@router.put("/items/{item_id}", tags=["Item"])
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
