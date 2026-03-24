# routes/auth.py
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional
from db import (
    create_user_email,
    create_user_google,
    login_email,
    login_google,
    logout,
    get_user_by_session,
    set_reset_token,
    reset_password,
)
from config import stocky_host
from dependencies import get_current_active_user

router = APIRouter(prefix="/auth")

HOST = stocky_host()


# ─────────────────────────────────────────
# REQUEST MODELS
# ─────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: str
    name: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


# ─────────────────────────────────────────
# EMAIL / PASSWORD
# ─────────────────────────────────────────

@router.post("/register")
def register(body: RegisterRequest):
    user_id = create_user_email(
        email=body.email,
        name=body.name,
        password=body.password
    )
    if user_id is None:
        raise HTTPException(status_code=409, detail="Email already registered")

    token = login_email(body.email, body.password)
    return {"ok": True, "session_token": token}


@router.post("/login")
def login(body: LoginRequest):
    token = login_email(body.email, body.password)
    if token is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"ok": True, "session_token": token}


@router.post("/logout")
def logout_user(user: dict = Depends(get_current_active_user)):
    logout(user["session_token"])
    return {"ok": True}


# ─────────────────────────────────────────
# GOOGLE OAUTH
# ─────────────────────────────────────────

@router.get("/google")
def google_login():
    """Redirect user to Google OAuth consent screen."""
    from config import get_google_client_id
    import urllib.parse

    params = urllib.parse.urlencode({
        "client_id":     get_google_client_id(),
        "redirect_uri":  f"{HOST}/auth/google/callback",
        "response_type": "code",
        "scope":         "openid email profile",
        "access_type":   "offline",
    })
    return RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?{params}")


@router.get("/google/callback")
def google_callback(code: str):
    """Handle Google OAuth callback, create/login user, redirect to frontend."""
    import requests
    from config import get_google_client_id, get_google_client_secret

    # exchange code for token
    token_response = requests.post("https://oauth2.googleapis.com/token", data={
        "code":          code,
        "client_id":     get_google_client_id(),
        "client_secret": get_google_client_secret(),
        "redirect_uri":  "{HOST}/auth/google/callback",
        "grant_type":    "authorization_code",
    })
    token_data = token_response.json()

    if "error" in token_data:
        raise HTTPException(status_code=400, detail="Google OAuth failed")

    # fetch user info from Google
    user_info = requests.get("https://www.googleapis.com/oauth2/v2/userinfo", headers={
        "Authorization": f"Bearer {token_data['access_token']}"
    }).json()

    # upsert user in db
    user_id = create_user_google(
        google_id=user_info["id"],
        email=user_info["email"],
        name=user_info.get("name"),
        avatar_url=user_info.get("picture")
    )

    # issue session token
    token = login_google(user_id)

    # redirect frontend with token in URL
    return RedirectResponse(f"http://localhost:3000/auth/callback?token={token}")


# ─────────────────────────────────────────
# PASSWORD RESET
# ─────────────────────────────────────────

@router.post("/forgot-password")
def forgot_password(body: ForgotPasswordRequest):
    token = set_reset_token(body.email)
    # always return ok so we don't reveal if email exists
    # send email with token here via your email service
    return {"ok": True}


@router.post("/reset-password")
def reset_password_route(body: ResetPasswordRequest):
    success = reset_password(body.token, body.new_password)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    return {"ok": True}


# ─────────────────────────────────────────
# CURRENT USER
# ─────────────────────────────────────────

@router.get("/me")
def get_me(user: dict = Depends(get_current_active_user)):
    """Returns the current authenticated user's profile."""
    return {
        "id":             user["id"],
        "email":          user["email"],
        "name":           user["name"],
        "avatar_url":     user["avatar_url"],
        "tier":           user["tier"],
        "tier_status":    user["tier_status"],
        "email_verified": bool(user["email_verified"]),
        "is_admin":       bool(user["is_admin"]),
    }