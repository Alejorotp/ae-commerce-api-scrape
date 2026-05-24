import cloudinary
import cloudinary.uploader
from app.config import settings


cloudinary.config(
    cloud_name=settings.cloudinary_cloud_name,
    api_key=settings.cloudinary_api_key,
    api_secret=settings.cloudinary_api_secret,
)


def upload_image(file):
    result = cloudinary.uploader.upload(file)
    return result["secure_url"]