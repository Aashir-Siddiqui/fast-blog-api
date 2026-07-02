from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.user import User
from app.schemas.user import UserResponse
from app.services.cloudinary_service import upload_image, delete_image

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
def get_profile(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/me/avatar", response_model=UserResponse)
async def update_avatar(
    avatar: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()

    # Delete old avatar if it was uploaded by us (not a Google/GitHub URL)
    if user.avatar_url and "cloudinary" in (user.avatar_url or ""):
        # We stored public_id separately only for blogs;
        # for avatars store public_id in a future migration — skip delete for now
        pass

    result = await upload_image(avatar, folder="avatars")
    user.avatar_url = result["url"]

    db.commit()
    db.refresh(user)
    return user


@router.get("/{user_id}/blogs")
def get_user_blogs(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user": user.name, "blogs": user.blogs}