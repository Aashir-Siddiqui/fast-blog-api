from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.schemas.user import UserResponse

class BlogCreate(BaseModel):
    title: str
    content: str
    
class BlogUpdate(BaseModel):
    title: Optional[str]
    content: Optional[str]

class BlogResponse(BaseModel):
    id: int
    title: str
    content: str
    cover_image_url: Optional[str]
    author: UserResponse
    created_at: datetime
    updated_at: Optional[datetime]
    model_config = {"from_attributes": True}

class PaginatedBlogs(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int
    data: list[BlogResponse]