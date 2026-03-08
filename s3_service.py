import boto3
import uuid
from fastapi import HTTPException
from sqlalchemy.orm import Session
from models import AWSConfig

def get_active_aws_config(db: Session):
    config = db.query(AWSConfig).filter(AWSConfig.is_active == True).first()
    if not config:
        raise HTTPException(status_code=500, detail="AWS config not found")
    return config

def upload_file_to_s3(upload_file, db: Session) -> str:
    try:
        config = get_active_aws_config(db)
        s3 = boto3.client(
            "s3",
            aws_access_key_id=config.aws_access_key_id,
            aws_secret_access_key=config.aws_secret_access_key,
            region_name=config.aws_region,
        )
        unique_name = f"properties/{uuid.uuid4()}-{upload_file.filename}"
        
        s3.upload_fileobj(
            upload_file.file,
            config.aws_s3_bucket,
            unique_name,
            ExtraArgs={"ContentType": upload_file.content_type}, 
        )
        return f"https://{config.aws_s3_bucket}.s3.{config.aws_region}.amazonaws.com/{unique_name}"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"S3 upload failed: {str(e)}")