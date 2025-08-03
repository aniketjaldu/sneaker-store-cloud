import fastapi
import requests
import jwt
import datetime
import hashlib
import os
from dotenv import load_dotenv
from fastapi import HTTPException, Header, Depends
from pydantic import BaseModel
from typing import Optional

app = fastapi.FastAPI()

load_dotenv()

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    print("WARNING: JWT_SECRET is not set!")
    JWT_SECRET = "super-secret-jwt-key"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRY_MINUTES = 15
REFRESH_TOKEN_EXPIRY_DAYS = 7

# Data models
class LoginRequest(BaseModel):
    email: str
    password: str

class RefreshRequest(BaseModel):
    refresh_token: str

# JWT Utility Functions
def create_access_token(user_id: int, email: str, role: str) -> str:
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "type": "access",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRY_MINUTES),
        "iat": datetime.datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def create_refresh_token(user_id: int, email: str, role: str) -> str:
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "type": "refresh",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=REFRESH_TOKEN_EXPIRY_DAYS),
        "iat": datetime.datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def extract_token_from_header(authorization: str) -> Optional[str]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    return authorization.split(" ")[1]

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

@app.get("/")
def read_root():
    return {"message": "IDP Service is running"}

@app.post("/login")
async def login(login_data: LoginRequest):
    try:
        # Call User Service to validate credentials
        response = requests.post("http://user-service:8080/users/login", json=login_data.dict())
        
        if response.status_code == 200:
            user_data = response.json()
            
            # Create tokens
            access_token = create_access_token(user_data["user_id"], user_data["email"], user_data["role"])
            refresh_token = create_refresh_token(user_data["user_id"], user_data["email"], user_data["role"])
            
            # Store refresh token in User Service
            token_data = {
                "user_id": user_data["user_id"],
                "token_hash": hash_token(refresh_token),
                "expires_at": (datetime.datetime.utcnow() + datetime.timedelta(days=REFRESH_TOKEN_EXPIRY_DAYS)).isoformat()
            }
            
            store_response = requests.post("http://user-service:8080/users/refresh-tokens", json=token_data)
            if store_response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to store refresh token")
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": ACCESS_TOKEN_EXPIRY_MINUTES * 60,
                "user": user_data
            }
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="User service unavailable")

@app.post("/verify")
async def verify_token(authorization: str = Header(None)):
    token = extract_token_from_header(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    payload = verify_jwt_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return payload

@app.post("/refresh")
async def refresh_token(refresh_data: RefreshRequest):
    try:
        # Verify refresh token
        payload = verify_jwt_token(refresh_data.refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        user_id = int(payload["sub"])
        
        # Verify refresh token exists in database
        verify_response = requests.post("http://user-service:8080/users/verify-refresh-token", 
                                      json={"token_hash": hash_token(refresh_data.refresh_token)})
        
        if verify_response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        # Create new tokens
        new_access_token = create_access_token(user_id, payload["email"], payload["role"])
        new_refresh_token = create_refresh_token(user_id, payload["email"], payload["role"])
        
        # Update refresh token in database
        update_data = {
            "old_token_hash": hash_token(refresh_data.refresh_token),
            "new_token_hash": hash_token(new_refresh_token),
            "expires_at": (datetime.datetime.utcnow() + datetime.timedelta(days=REFRESH_TOKEN_EXPIRY_DAYS)).isoformat()
        }
        
        update_response = requests.put("http://user-service:8080/users/refresh-tokens", json=update_data)
        if update_response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to update refresh token")
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRY_MINUTES * 60
        }
        
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="User service unavailable")

@app.post("/logout")
async def logout(authorization: str = Header(None)):
    try:
        token = extract_token_from_header(authorization)
        if not token:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        payload = verify_jwt_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Delete refresh token from database
        delete_response = requests.delete("http://user-service:8080/users/refresh-tokens", 
                                        json={"token_hash": hash_token(token)})
        
        return {"message": "Logout successful"}
        
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="User service unavailable")

@app.post("/admin/login")
async def admin_login(login_data: LoginRequest):
    try:
        # Call User Service to validate admin credentials
        response = requests.post("http://user-service:8080/users/admin/login", json=login_data.dict())
        
        if response.status_code == 200:
            user_data = response.json()
            
            # Create tokens
            access_token = create_access_token(user_data["user_id"], user_data["email"], "admin")
            refresh_token = create_refresh_token(user_data["user_id"], user_data["email"], "admin")
            
            # Store refresh token in User Service
            token_data = {
                "user_id": user_data["user_id"],
                "token_hash": hash_token(refresh_token),
                "expires_at": (datetime.datetime.utcnow() + datetime.timedelta(days=REFRESH_TOKEN_EXPIRY_DAYS)).isoformat()
            }
            
            store_response = requests.post("http://user-service:8080/users/refresh-tokens", json=token_data)
            if store_response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to store refresh token")
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": ACCESS_TOKEN_EXPIRY_MINUTES * 60,
                "user": user_data
            }
        else:
            raise HTTPException(status_code=401, detail="Invalid admin credentials")
            
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="User service unavailable")