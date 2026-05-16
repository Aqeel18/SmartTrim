"""
Auth routes — SmartTrim 360 Phase 3.

Endpoints
---------
POST /auth/register   Create a new account
POST /auth/token      Login → returns JWT access token
GET  /auth/me         Return current authenticated user profile
PUT  /auth/me         Update display name
DELETE /auth/me       Deactivate account (soft delete)
"""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.auth import (
    create_access_token, hash_password, verify_password,
    get_current_user, TOKEN_EXPIRE,
)
from app.db.session import get_db
from app.db.models import User

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

# ─── Schemas ──────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email:        EmailStr
    password:     str
    display_name: str | None = None


class UserOut(BaseModel):
    id:           str
    email:        str
    display_name: str | None
    is_active:    bool

    class Config:
        from_attributes = True


class TokenOut(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    expires_in:   int           # seconds


class UpdateProfileRequest(BaseModel):
    display_name: str | None = None

# ─── Routes ───────────────────────────────────────────────────────────────────

@auth_router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    """Create a new SmartTrim 360 account."""
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )
    user = User(
        email        = body.email,
        hashed_pw    = hash_password(body.password),
        display_name = body.display_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@auth_router.post("/token", response_model=TokenOut)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db:   Session                   = Depends(get_db),
):
    """Authenticate with email + password, return a JWT access token."""
    user = db.query(User).filter(User.email == form.username, User.is_active == True).first()
    if user is None or not verify_password(form.password, user.hashed_pw):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(subject=user.id, expires_delta=timedelta(minutes=TOKEN_EXPIRE))
    return {"access_token": token, "token_type": "bearer", "expires_in": TOKEN_EXPIRE * 60}


@auth_router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return current_user


@auth_router.put("/me", response_model=UserOut)
def update_me(
    body:         UpdateProfileRequest,
    current_user: User    = Depends(get_current_user),
    db:           Session = Depends(get_db),
):
    """Update the authenticated user's display name."""
    if body.display_name is not None:
        current_user.display_name = body.display_name
    db.commit()
    db.refresh(current_user)
    return current_user


@auth_router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_me(
    current_user: User    = Depends(get_current_user),
    db:           Session = Depends(get_db),
):
    """Soft-delete the authenticated user account."""
    current_user.is_active = False
    db.commit()
