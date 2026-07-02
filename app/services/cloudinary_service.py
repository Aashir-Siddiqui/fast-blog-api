import cloudinary
import cloudinary.uploader
from fastapi import UploadFile, HTTPException
from app.core.config import settings

cloudinary.config(
    cloud_name = settings.CLOUDINARY_CLOUD_NAME,
    api_key = settings.CLOUDINARY_API_KEY,
    api_secret = settings.CLOUDINARY_API_SECRET
)

ALLOWED_TYPES = ["image.jpeg", "image/png", "image/web", "image/gif"]
MAX_FILE_SIZE = 25 * 1024 * 1024

async def upload_image(file: UploadFile, folder: str = "blog-covers") -> dict:
    """Upload an image to Cloudinary and return url + public_id."""

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Allowed: JPEG, PNG, WEBP, GIF"
        )
        
    contents = await file.read()

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File size exceeds 5MB limit"
        )

    result = cloudinary.uploader.upload(
        contents,
        folder=folder,
        resource_type = "image",
        transformation = [
            {"width": 1200, "height": 630, "crop": "fill", "gravity": "auto"},
            {"quality": "auto:good"},
            {"fetch_format": "auto"}
        ]
    )
    
    return {
        "url": result["secur_url"],
        "public_id": result["public_id"]
    }

def delete_image(public_id: str) -> None:
    """Delete an image from Cloudinary by its public_id."""
    cloudinary.uploader.destroy(public_id)