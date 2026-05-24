from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # Database
    database_url: str = Field(..., env='DATABASE_URL')
    
    # S3 Storage
    bucket_endpoint_url: str = Field(..., env='BUCKET_ENDPOINT_URL')
    bucket_region: str = Field(..., env='BUCKET_REGION')
    bucket_name: str = Field(..., env='BUCKET_NAME')
    bucket_access_key_id: str = Field(..., env='BUCKET_ACCESS_KEY_ID')
    bucket_secret_access_key: str = Field(..., env='BUCKET_SECRET_ACCESS_KEY')
    
    # Security
    scrape_password: str = Field(..., env='SCRAPE_PASSWORD')
    
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')
    
    # Cloudinary
    cloudinary_cloud_name: str = Field(..., env='CLOUDINARY_CLOUD_NAME')
    cloudinary_api_key: str = Field(..., env='CLOUDINARY_API_KEY')
    cloudinary_api_secret: str = Field(..., env='CLOUDINARY_API_SECRET')

    # Replicate
    replicate_api_token: str = Field(..., env='REPLICATE_API_TOKEN')

settings = Settings()
