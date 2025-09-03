import logging
import os
from typing import Tuple

from app.core.firebase import get_bucket

logger = logging.getLogger(__name__)


def upload_file(local_path: str, dest_path: str, content_type: str) -> str:
    bucket = get_bucket()
    blob = bucket.blob(dest_path)
    blob.upload_from_filename(local_path, content_type=content_type)
    logger.info("Uploaded file to %s", dest_path)
    return dest_path


def download_file(storage_path: str, local_path: str) -> str:
    bucket = get_bucket()
    blob = bucket.blob(storage_path)
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    blob.download_to_filename(local_path)
    logger.info("Downloaded %s to %s", storage_path, local_path)
    return local_path


def get_public_url(storage_path: str) -> str:
    bucket = get_bucket()
    blob = bucket.blob(storage_path)
    if not blob.exists():
        raise FileNotFoundError(storage_path)
    url = blob.generate_signed_url(expiration=3600)
    return url
