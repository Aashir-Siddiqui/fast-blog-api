from sqlalchemy import Column, Integer, String, Enum, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base

class AuthProvider(str, enum.Enum):
    local = "local"
    github = "github"
    google = "googel"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    provider = Column(Enum(AuthProvider), default=AuthProvider.local, nullable=False)
    provider_id = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_onupdate=func.now())
    blogs = relationship("Blog", back_populates="author", cascade="all, delete-orphan")