from typing import List
from fastapi import Depends, HTTPException
from fastapi.params import Form
from sqlalchemy.orm import Session
from fastapi import File, UploadFile
from src.Profile import crud, schemas
from src.Profile.dependencies import get_db, get_current_user, oauth2_scheme
from PIL import Image

from fastapi import APIRouter


router = APIRouter(prefix="/profiles")


@router.post("/create_profile/", tags=["User Profile"])
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


@router.get("/user_profile/", tags=["User Profile"])
def get_profile(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    current_user = get_current_user(db=db, token=token)
    db_user_profile = crud.get_user_profile(db=db, user_id=current_user.id)
    if db_user_profile is None:
        return HTTPException(status_code=401, detail="Bill does not exist")
    return db_user_profile


@router.get(
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


@router.delete("/UserProfile/{profile_id}", tags=["User Profile"])
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


@router.put("/profile/{profile_id}", tags=["User Profile"])
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
