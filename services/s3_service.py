import boto3
import os
import uuid
from werkzeug.utils import secure_filename

# Create an S3 client using credentials from .env
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)

BUCKET_NAME = os.getenv('AWS_S3_BUCKET')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def allowed_file(filename):
    """Check if the file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def upload_image(file, folder='products'):
    """
    Upload an image to S3 and return the public URL.

    Args:
        file: The file object from the request
        folder: The folder inside the S3 bucket to store the image

    Returns:
        The public URL of the uploaded image
    """
    if not allowed_file(file.filename):
        raise ValueError(f'File type not allowed. Allowed types: {ALLOWED_EXTENSIONS}')

    # Generate a unique filename to prevent overwrites
    # e.g. products/a1b2c3d4-e5f6-7890-abcd-ef1234567890.jpg
    extension = file.filename.rsplit('.', 1)[1].lower()
    unique_filename = f'{folder}/{uuid.uuid4()}.{extension}'

    # Upload to S3
    s3_client.upload_fileobj(
        file,
        BUCKET_NAME,
        unique_filename,
        ExtraArgs={'ContentType': file.content_type}
    )

    # Build and return the public URL
    url = f'https://{BUCKET_NAME}.s3.{os.getenv("AWS_REGION")}.amazonaws.com/{unique_filename}'
    return url


def delete_image(image_url):
    """
    Delete an image from S3 using its URL.

    Args:
        image_url: The full public URL of the image to delete
    """
    # Extract the key from the URL
    key = image_url.split(f'{BUCKET_NAME}.s3.{os.getenv("AWS_REGION")}.amazonaws.com/')[-1]

    s3_client.delete_object(
        Bucket=BUCKET_NAME,
        Key=key
    )