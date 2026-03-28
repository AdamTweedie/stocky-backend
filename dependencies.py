# dependencies.py
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from db import get_user_by_session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    user = get_user_by_session(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session token")
    return user


def get_current_active_user(token: str = Depends(oauth2_scheme)) -> dict:
    user = get_current_user(token)
    if not user["is_active"]:
        raise HTTPException(status_code=403, detail="Account is disabled")
    return user


def require_pro(token: str = Depends(oauth2_scheme)) -> dict:
    user = get_current_active_user(token)
    if user["tier"] not in ("pro", "enterprise"):
        raise HTTPException(status_code=403, detail="This feature requires a pro subscription")
    return user