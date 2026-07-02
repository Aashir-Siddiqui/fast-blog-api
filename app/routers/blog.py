import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.blog import Blog
from app.models.user import User
from app.schemas.blog import BlogResponse, PaginatedBlogs
from app.services.cloudinary_service import upload_image, delete_image

router = APIRouter(prefix="/blogs", tags=["Blogs"])


def get_blog_or_404(blog_id: int, db: Session) -> Blog:
    blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    return blog


# ── Public ────────────────────────────────────────────────────────────────────

@router.get("", response_model=PaginatedBlogs)
def list_blogs(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    search: str = Query(default=""),
    author_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(Blog)

    if search:
        query = query.filter(Blog.title.ilike(f"%{search}%"))

    if author_id:
        query = query.filter(Blog.author_id == author_id)

    total = query.count()
    blogs = query.order_by(Blog.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    return PaginatedBlogs(
        page=page,
        limit=limit,
        total=total,
        total_pages=math.ceil(total / limit) if total else 0,
        data=blogs,
    )


@router.get("/{blog_id}", response_model=BlogResponse)
def get_blog(blog_id: int, db: Session = Depends(get_db)):
    return get_blog_or_404(blog_id, db)


# ── Protected ─────────────────────────────────────────────────────────────────

@router.post("", response_model=BlogResponse, status_code=status.HTTP_201_CREATED)
async def create_blog(
    title: str = Form(...),
    content: str = Form(...),
    cover_image: Optional[UploadFile] = File(default=None),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    image_url = None
    image_public_id = None

    if cover_image and cover_image.filename:
        result = await upload_image(cover_image)
        image_url = result["url"]
        image_public_id = result["public_id"]

    blog = Blog(
        title=title,
        content=content,
        cover_image_url=image_url,
        cover_image_public_id=image_public_id,
        author_id=user_id,
    )
    db.add(blog)
    db.commit()
    db.refresh(blog)
    return blog


@router.put("/{blog_id}", response_model=BlogResponse)
async def update_blog(
    blog_id: int,
    title: Optional[str] = Form(default=None),
    content: Optional[str] = Form(default=None),
    cover_image: Optional[UploadFile] = File(default=None),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    blog = get_blog_or_404(blog_id, db)

    if blog.author_id != user_id:
        raise HTTPException(status_code=403, detail="You don't have permission to edit this blog")

    if title:
        blog.title = title
    if content:
        blog.content = content

    if cover_image and cover_image.filename:
        # Delete old image from Cloudinary first
        if blog.cover_image_public_id:
            delete_image(blog.cover_image_public_id)

        result = await upload_image(cover_image)
        blog.cover_image_url = result["url"]
        blog.cover_image_public_id = result["public_id"]

    db.commit()
    db.refresh(blog)
    return blog


@router.delete("/{blog_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_blog(
    blog_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    blog = get_blog_or_404(blog_id, db)

    if blog.author_id != user_id:
        raise HTTPException(status_code=403, detail="You don't have permission to delete this blog")

    # Delete associated image from Cloudinary
    if blog.cover_image_public_id:
        delete_image(blog.cover_image_public_id)

    db.delete(blog)
    db.commit()


# ── Image-only upload (for rich text editors) ─────────────────────────────────

@router.post("/upload-image")
async def upload_blog_image(
    image: UploadFile = File(...),
    _: int = Depends(get_current_user_id),
):
    result = await upload_image(image, folder="blog-content")
    return {"url": result["url"]}