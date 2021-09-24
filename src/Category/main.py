from typing import List
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from src.Category import crud, schemas


from src.Category.dependencies import oauth2_scheme, get_current_user, get_db
from fastapi import APIRouter


router = APIRouter(prefix="/categories")


@router.post("/users/", tags=["Category"])
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


@router.get("/categorys", response_model=List[schemas.Category], tags=["Category"])
def get_categorys(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    category = crud.get_categorys(db, skip=skip, limit=limit)

    return category


@router.get(
    "/category/{category_id}", response_model=schemas.Category, tags=["Category"]
)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    category = crud.get_category(db=db, category_id=category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="category does not exist")
    return category


@router.delete("/category/{category_id}", tags=["Category"])
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


@router.put("/categorys/{category_id}", tags=["Category"])
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
