from datetime import datetime, timedelta, timezone
from typing import Optional, Any, List

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer # Import OAuth2PasswordBearer
from sqlalchemy.orm import Session # Needed for db session in get_current_user

from .core.config import settings
from . import models, schemas, services # For services.get_user_by_username and models.User
from .db.session import get_db # To get db session

# Define oauth2_scheme here
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login/token")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = settings.ALGORITHM
SECRET_KEY = settings.SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[schemas.TokenData]: # Use TokenData schema
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Validate payload against TokenData schema if needed, or directly extract
        username: Optional[str] = payload.get("sub")
        user_id: Optional[str] = payload.get("user_id") # Ensure this is in your token data
        if username is None: # Username ("sub") is standard for JWT subject
             return None # Or raise error, depending on how TokenData is defined
        return schemas.TokenData(username=username, user_id=user_id)
    except JWTError:
        return None

# Moved from routers/auth.py
async def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = decode_access_token(token)
    if not token_data or not token_data.username: # Check if token_data and username are valid
        raise credentials_exception
    
    user = services.get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

# Moved from routers/auth.py
async def get_current_active_user(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    # Explicitly load roles here if not automatically handled by UserDisplay schema or if needed before response model
    # This ensures roles are available for RBAC checks that might happen before serialization.
    # For example, by accessing current_user.roles. This will trigger lazy load if session is active.
    _ = current_user.roles # Access roles to trigger lazy load
    return current_user

# RBAC Dependency
def require_role(required_role_name: str):
    """
    Dependency that checks if the current active user has the required role.
    """
    async def role_checker(
        current_user: models.User = Depends(get_current_active_user) # Now uses get_current_active_user from this file
    ):
        if not hasattr(current_user, 'roles'):
             # This case should ideally be prevented by get_current_active_user loading roles or by ORM config
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User roles not loaded.")

        user_role_names = {role.role_name for role in current_user.roles}
        if required_role_name not in user_role_names:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Requires role: '{required_role_name}'. User has roles: {', '.join(user_role_names) if user_role_names else 'None'}.",
            )
        return current_user
    return role_checker
