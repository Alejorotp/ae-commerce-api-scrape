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

async def get_presigned_url(image_key: str, expires_in: int = 3600) -> str:
    """Generate a presigned URL for an image."""
    session = aioboto3.Session()
    try:
        async with session.client(
            "s3",
            endpoint_url=settings.bucket_endpoint_url,
            region_name=settings.bucket_region,
            aws_access_key_id=settings.bucket_access_key_id,
            aws_secret_access_key=settings.bucket_secret_access_key,
        ) as client:
            url = await client.generate_presigned_url(
                "get_object",
                Params={"Bucket": settings.bucket_name, "Key": image_key},
                ExpiresIn=expires_in,
            )
            return url
    except Exception as e:
        logger.error(f"Failed to generate presigned URL for {image_key}: {e}")
        return None
