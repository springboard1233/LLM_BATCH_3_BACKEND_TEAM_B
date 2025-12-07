import sys
import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel
import bcrypt
from bson import ObjectId

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", "..", "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.utils.fraud_dashboard.database import get_collection

# Using bcrypt directly instead of passlib to avoid compatibility issues
def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    # Ensure password is within bcrypt's 72-byte limit
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a bcrypt hash"""
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    return bcrypt.checkpw(password_bytes, hashed_password.encode('utf-8'))

router = APIRouter(prefix="/auth", tags=["Auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None
    role: Optional[str] = "analyst"

class UserPublic(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    role: Optional[str] = None


def get_users_collection():
    return get_collection("users")


def get_user_by_email(email: str):
    col = get_users_collection()
    doc = col.find_one({"email": email})
    if not doc:
        return None
    doc["id"] = str(doc.get("_id"))
    return doc


def get_user_by_id(user_id: str):
    col = get_users_collection()
    try:
        oid = ObjectId(user_id)
    except Exception:
        return None
    doc = col.find_one({"_id": oid})
    if not doc:
        return None
    doc["id"] = str(doc.get("_id"))
    return doc


# Simple auth - no JWT needed, frontend stores user data in localStorage


@router.post("/login")
async def login(data: LoginRequest):
    user = get_user_by_email(data.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if "password" not in user:
        raise HTTPException(status_code=500, detail="User password not set")

    if not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Simple auth - just return user data, frontend stores in localStorage
    return {
        "user": {
            "id": str(user["id"]),
            "email": user["email"],
            "full_name": user.get("full_name"),
            "role": user.get("role"),
        }
    }


@router.post("/register")
async def register(data: RegisterRequest):
    print(f"=== REGISTER API CALLED ===")
    print(f"Email: {data.email}")
    print(f"Full name: {data.full_name}")
    print(f"Role: {data.role}")
    
    try:
        col = get_users_collection()
        print(f"✓ Got users collection: {col.name}")

        existing = col.find_one({"email": data.email})
        if existing:
            print(f"✗ User already exists: {data.email}")
            raise HTTPException(status_code=400, detail="User already exists")
        print(f"✓ User does not exist, proceeding with registration")

        print(f"Password length: {len(data.password)} chars, {len(data.password.encode('utf-8'))} bytes")
        print(f"Password type: {type(data.password)}")
        
        try:
            hashed_password = hash_password(data.password)
            print(f"✓ Password hashed successfully")
        except Exception as hash_error:
            print(f"✗ Password hashing failed: {type(hash_error).__name__}: {hash_error}")
            raise

        doc = {
            "email": data.email,
            "password": hashed_password,
            "full_name": data.full_name,
            "role": data.role or "analyst",
            "created_at": datetime.utcnow(),
        }
        print(f"✓ Document prepared: {doc.keys()}")

        insert_result = col.insert_one(doc)
        user_id = str(insert_result.inserted_id)
        print(f"✓ User inserted with ID: {user_id}")

        print(f"=== REGISTER API SUCCESS ===")
        # Simple auth - just return user data, frontend stores in localStorage
        return {
            "user": {
                "id": user_id,
                "email": data.email,
                "full_name": data.full_name,
                "role": data.role or "analyst",
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"✗ REGISTER API ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@router.post("/logout")
async def logout():
    # Simple auth - frontend clears localStorage
    return {"message": "Logged out"}


@router.get("/me")
async def me(user_id: Optional[str] = Query(None)):
    # Simple auth - accept user_id as query param (optional)
    # Frontend sends user_id from localStorage
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserPublic(
        id=str(user["id"]),
        email=user["email"],
        full_name=user.get("full_name"),
        role=user.get("role"),
    )


