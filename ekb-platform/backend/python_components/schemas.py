from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
import uuid
from datetime import datetime

# Role Schemas
class RoleBase(BaseModel):
    role_name: str = Field(..., min_length=3, max_length=50)
    description: Optional[str] = None

class RoleCreate(RoleBase):
    pass

class RoleDisplay(RoleBase):
    role_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    username: Optional[str] = Field(None, min_length=3, max_length=50) # Optional if using email as primary or for SSO linking
    full_name: Optional[str] = Field(None, max_length=100)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    username: str = Field(..., min_length=3, max_length=50) # Make username mandatory for local signup

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None

class UserDisplay(UserBase):
    user_id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    roles: Optional[List[RoleDisplay]] = [] # Display roles associated with the user

    class Config:
        orm_mode = True

class UserInDBBase(UserBase):
    user_id: uuid.UUID
    is_active: bool = True
    hashed_password: Optional[str] = None
    sso_provider: Optional[str] = None
    sso_subject_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        orm_mode = True

# Used for internal representation, includes hashed_password
class UserInDB(UserInDBBase):
    hashed_password: str


# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[str] = None # Keep as string if UUID is serialized as string in token
    # Add scopes if using OAuth2 scopes
    # scopes: List[str] = []

# Schema for assigning/revoking roles
class UserRoleOperation(BaseModel):
    role_name: str = Field(..., min_length=3, max_length=50)


# For OAuth2PasswordRequestForm, FastAPI provides this, but good to know its structure
# class OAuth2PasswordRequestForm(BaseModel):
#     username: str
#     password: str
#     scope: str = ""
#     client_id: Optional[str] = None
#     client_secret: Optional[str] = None
#     grant_type: str = "password" # Must be password for token endpoint
