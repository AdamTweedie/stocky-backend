# routes/users.py
# routes/users.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from db import (
    get_user_by_id,
    update_user_profile,
    update_password,
    get_token_usage,
    get_followed_industries,
    follow_industry,
    unfollow_industry,
    get_followed_stocks,
    follow_stock,
    unfollow_stock,
    reorder_stocks,
    update_subscription,
    cancel_subscription,
    get_user_feed_filters,
)
from dependencies import get_current_active_user
import bcrypt

router = APIRouter(prefix="/user")


# ─────────────────────────────────────────
# RESPONSE MODELS
# ─────────────────────────────────────────

class UserProfileResponse(BaseModel):
    id: int
    email: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    email_verified: bool
    tier: str
    tier_status: str
    subscription_start: Optional[str] = None
    subscription_renewal: Optional[str] = None
    subscription_end: Optional[str] = None
    is_active: bool
    is_admin: bool


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    avatar_url: Optional[str] = None


class UpdatePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class FollowIndustryRequest(BaseModel):
    industry: str


class ReorderStocksRequest(BaseModel):
    ordered_short_names: list[str]


class TokenUsageResponse(BaseModel):
    used: int
    limit: int
    remaining: int
    reset_at: Optional[str] = None


class SubscriptionResponse(BaseModel):
    tier: str
    tier_status: str
    subscription_id: Optional[str] = None
    subscription_start: Optional[str] = None
    subscription_renewal: Optional[str] = None
    subscription_end: Optional[str] = None


def db_to_profile(user: dict) -> UserProfileResponse:
    return UserProfileResponse(
        id=user["id"],
        email=user["email"],
        name=user["name"],
        avatar_url=user["avatar_url"],
        email_verified=bool(user["email_verified"]),
        tier=user["tier"],
        tier_status=user["tier_status"],
        subscription_start=user["subscription_start"],
        subscription_renewal=user["subscription_renewal"],
        subscription_end=user["subscription_end"],
        is_active=bool(user["is_active"]),
        is_admin=bool(user["is_admin"])
    )


# ─────────────────────────────────────────
# PROFILE
# ─────────────────────────────────────────

@router.get("/profile", response_model=UserProfileResponse)
def get_profile(user: dict = Depends(get_current_active_user)):
    return db_to_profile(user)


@router.put("/profile", response_model=UserProfileResponse)
def update_profile(
    body: UpdateProfileRequest,
    user: dict = Depends(get_current_active_user)
):
    update_user_profile(user["id"], **body.model_dump(exclude_none=True))
    updated = get_user_by_id(user["id"])
    return db_to_profile(updated)


@router.put("/password")
def change_password(
    body: UpdatePasswordRequest,
    user: dict = Depends(get_current_active_user)
):
    if not user["password_hash"]:
        raise HTTPException(status_code=400, detail="Account uses Google OAuth, no password to update")

    if not bcrypt.checkpw(body.current_password.encode(), user["password_hash"].encode()):
        raise HTTPException(status_code=401, detail="Current password is incorrect")

    update_password(user["id"], body.new_password)
    return {"ok": True}


# ─────────────────────────────────────────
# TOKEN USAGE
# ─────────────────────────────────────────

@router.get("/tokens", response_model=TokenUsageResponse)
def get_tokens(user: dict = Depends(get_current_active_user)):
    usage = get_token_usage(user["id"])
    if not usage:
        raise HTTPException(status_code=404, detail="User not found")
    return TokenUsageResponse(**usage)


# ─────────────────────────────────────────
# WATCHLIST
# ─────────────────────────────────────────

@router.get("/watchlist")
def get_watchlist(user: dict = Depends(get_current_active_user)):
    return {"results": get_followed_stocks(user["id"])}


@router.post("/watchlist")
def add_to_watchlist(
    body: dict,
    user: dict = Depends(get_current_active_user)
):
    short_name = body.get("short_name")
    if not short_name:
        raise HTTPException(status_code=400, detail="short_name is required")

    result = follow_stock(user["id"], short_name)
    if not result:
        raise HTTPException(status_code=409, detail="Stock already in watchlist")
    return {"ok": True}


@router.delete("/watchlist/{short_name}")
def remove_from_watchlist(
    short_name: str,
    user: dict = Depends(get_current_active_user)
):
    result = unfollow_stock(user["id"], short_name)
    if not result:
        raise HTTPException(status_code=404, detail="Stock not found in watchlist")
    return {"ok": True}


@router.put("/watchlist/reorder")
def reorder_watchlist(
    body: ReorderStocksRequest,
    user: dict = Depends(get_current_active_user)
):
    reorder_stocks(user["id"], body.ordered_short_names)
    return {"ok": True}


# ─────────────────────────────────────────
# INDUSTRIES
# ─────────────────────────────────────────

@router.get("/industries")
def get_industries(user: dict = Depends(get_current_active_user)):
    return {"results": get_followed_industries(user["id"])}


@router.post("/industries")
def add_industry(
    body: FollowIndustryRequest,
    user: dict = Depends(get_current_active_user)
):
    result = follow_industry(user["id"], body.industry)
    if not result:
        raise HTTPException(status_code=409, detail="Industry already followed")
    return {"ok": True}


@router.delete("/industries/{industry}")
def remove_industry(
    industry: str,
    user: dict = Depends(get_current_active_user)
):
    result = unfollow_industry(user["id"], industry)
    if not result:
        raise HTTPException(status_code=404, detail="Industry not found")
    return {"ok": True}


# ─────────────────────────────────────────
# SUBSCRIPTION
# ─────────────────────────────────────────

@router.get("/subscription", response_model=SubscriptionResponse)
def get_subscription(user: dict = Depends(get_current_active_user)):
    return SubscriptionResponse(
        tier=user["tier"],
        tier_status=user["tier_status"],
        subscription_id=user["subscription_id"],
        subscription_start=user["subscription_start"],
        subscription_renewal=user["subscription_renewal"],
        subscription_end=user["subscription_end"]
    )


# ─────────────────────────────────────────
# FEED FILTERS (watchlist + industries combined)
# ─────────────────────────────────────────

@router.get("/feed-filters")
def get_feed_filters(user: dict = Depends(get_current_active_user)):
    """
    Returns both followed stocks and industries in one call.
    Useful for initialising the frontend feed on login.
    """
    return get_user_feed_filters(user["id"])
