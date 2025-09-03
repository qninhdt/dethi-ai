import logging
import os
from typing import Optional
from dotenv import load_dotenv

import firebase_admin
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth, credentials, firestore, storage

logger = logging.getLogger(__name__)

_initialized = False


def init_firebase() -> None:
    global _initialized
    if _initialized:
        return
    # Load env when initializing (works for both API and worker processes)
    load_dotenv()
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not os.path.exists(cred_path):
        logger.error("Firebase credentials not found at %s", cred_path)
        raise RuntimeError("Missing Firebase credentials")
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(
        cred,
        {
            "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET", ""),
        },
    )
    _initialized = True
    logger.info("Firebase initialized")


def get_firestore() -> firestore.Client:
    return firestore.client()


def get_bucket():
    return storage.bucket()


bearer_scheme = HTTPBearer(auto_error=False)


async def firebase_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
):
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Missing or invalid auth token")
    token = credentials.credentials
    try:
        decoded = auth.verify_id_token(token)
        if "firebase" not in decoded:
            raise HTTPException(status_code=403, detail="Invalid Firebase token")
        provider = decoded.get("firebase", {}).get("sign_in_provider")
        if provider != "google.com":
            raise HTTPException(status_code=403, detail="Only Google auth is allowed")
        return decoded
    except Exception as e:  # noqa: BLE001
        logger.exception("Auth verification failed")
        raise HTTPException(status_code=401, detail="Unauthorized") from e
