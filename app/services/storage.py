import aioboto3
from app.config import settings
import logging

logger = logging.getLogger(__name__)

async def upload_image_to_s3(image_bytes: bytes, filename: str, content_type: str = "image/jpeg") -> str:
    """Uploads an image to S3 and returns its public bucket URL."""
    session = aioboto3.Session()
    
    # We construct the URL manually if public
    # Endpoint structure might vary, typical path-style:
    public_url = f"{settings.bucket_endpoint_url}/{settings.bucket_name}/{filename}"
    
    try:
        async with session.client(
            "s3",
            endpoint_url=settings.bucket_endpoint_url,
            region_name=settings.bucket_region,
            aws_access_key_id=settings.bucket_access_key_id,
            aws_secret_access_key=settings.bucket_secret_access_key,
        ) as client:
            await client.put_object(
                Bucket=settings.bucket_name,
                Key=filename,
                Body=image_bytes,
                ContentType=content_type,
                ACL="public-read" # Assuming we want public read
            )
            return public_url
    except Exception as e:
        logger.error(f"Failed to upload {filename} to S3: {e}")
        return None
