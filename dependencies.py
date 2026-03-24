from fastapi import Header, HTTPException
from db import get_user_by_session


def get_current_user(authorisation: str = Header(None)) -> dict:
    """
    Extract and validate the current user from the session token.
    Raises 401 if token is missing or invalid.
    """

    if not authorisation:
        raise HTTPException(status_code=401, detail="Not authenticated")


    # expect "Bearer <token>"
    parts = authorisation.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = parts[1]
    user = get_user_by_session(token)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session token")

    return user


def get_current_active_user(authorization: str = Header(None)) -> dict:
    """Same as get_current_user but also checks is_active."""
    user = get_current_user(authorization)
    if not user["is_active"]:
        raise HTTPException(status_code=403, detail="Account is disabled")
    return user


def require_pro(authorization: str = Header(None)) -> dict:
    """Only allows pro or enterprise users through."""
    user = get_current_active_user(authorization)
    if user["tier"] not in ("pro", "enterprise"):
        raise HTTPException(status_code=403, detail="This feature requires a pro subscription")
    return user