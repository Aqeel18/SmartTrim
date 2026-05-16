"""
JWT Authentication — SmartTrim 360 Phase 3.

Provides:
  - Password hashing / verification (bcrypt via passlib)
  - JWT access token creation and validation (python-jose)
  - FastAPI dependency `get_current_user` for protected routes

Environment variables:
  SECRET_KEY          Random secret (min 32 chars). Generate with:
                      python -c "import secrets; print(secrets.token_hex(32))"
  ACCESS_TOKEN_EXPIRE_MINUTES  Default: 60
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User

# ─── Config ───────────────────────────────────────────────────────────────────

SECRET_KEY    = os.getenv("SECRET_KEY", "CHANGE_ME_IN_PRODUCTION_use_secrets_token_hex_32")
ALGORITHM     = "HS256"
TOKEN_EXPIRE  = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

pwd_ctx       = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# ─── Password helpers ─────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return pwd_ctx.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)

# ─── Token helpers ────────────────────────────────────────────────────────────

def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token."""
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=TOKEN_EXPIRE))
    payload = {"sub": subject, "exp": expire, "iat": datetime.now(timezone.utc)}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> str:
    """Decode and validate a JWT. Returns the subject (user_id) or raises."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub: str = payload.get("sub")
        if sub is None:
            raise ValueError("Missing subject claim")
        return sub
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

# ─── FastAPI dependency ───────────────────────────────────────────────────────

def get_current_user(
    token: str    = Depends(oauth2_scheme),
    db:   Session = Depends(get_db),
) -> User:
    """
    Protected-route dependency.

    Usage:
        @router.get("/me")
        async def me(user: User = Depends(get_current_user)):
            return {"email": user.email}
    """
    user_id = decode_token(token)
    user    = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
