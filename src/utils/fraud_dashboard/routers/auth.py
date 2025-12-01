# src/utils/fraud_dashboard/routers/auth.py

from datetime import datetime, timedelta
from typing import Dict, Optional

import os
import jwt
from fastapi import APIRouter, HTTPException, status
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field

from src.utils.fraud_dashboard.database import get_collection

router = APIRouter(prefix="/auth", tags=["Auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("JWT_SECRET", "change-me")  # set in .env for production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "8"))


def hash_password(password: str) -> str:
    password = password[:72]
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: Dict, expires_delta: Optional[timedelta] = None
) -> str:
    """
    Creates a signed JWT access token with an expiration.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserPublic(BaseModel):
    id: str
    email: EmailStr
    name: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class SignupResponse(BaseModel):
    status: str
    user_id: str
    email: EmailStr
    name: Optional[str] = None


@router.post("/signup", response_model=SignupResponse)
async def signup(payload: SignupRequest):
    email = payload.email.strip().lower()
    password = payload.password
    name = (payload.name or "").strip()

    users = get_collection("users")

    # Check for existing user
    if users.find_one({"email": email}):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists",
        )

    hashed = hash_password(password[:72])
    doc = {
        "email": email,
        "password": hashed,
        "name": name,
        "created_at": datetime.utcnow(),
    }

    res = users.insert_one(doc)

    return {
        "status": "ok",
        "user_id": str(res.inserted_id),
        "email": email,
        "name": name or None,
    }


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest):
    email = payload.email.strip().lower()
    password = payload.password

    users = get_collection("users")
    user = users.find_one({"email": email})

    if not user or not verify_password(password, user.get("password", "")):
        # Add WWW-Authenticate header for proper 401 semantics
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token({"sub": str(user["_id"]), "email": email})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": str(user["_id"]),
            "email": user["email"],
            "name": user.get("name"),
        },
    }
