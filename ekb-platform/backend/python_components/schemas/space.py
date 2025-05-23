import uuid
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from .user import UserDisplay # For displaying user details (e.g., creator)
from .user import RoleDisplay # For displaying role details within a space context

# Base schema for Space properties
class SpaceBase(BaseModel):
    space_name: str = Field(..., min_length=3, max_length=100, description="Name of the space")
    space_type: str = Field(..., min_length=3, max_length=50, description="Type of the space (e.g., 'project', 'team')")
    description: Optional[str] = Field(None, description="Optional description of the space")

# Schema for creating a new space
class SpaceCreate(SpaceBase):
    pass

# Schema for displaying space information, including the creator
class SpaceDisplay(SpaceBase):
    space_id: uuid.UUID
    created_by_user_id: Optional[uuid.UUID] # Made optional to handle if creator is SET NULL
    created_at: datetime
    updated_at: datetime
    creator: Optional[UserDisplay] = None # To display creator's details

    class Config:
        orm_mode = True

# Schema for assigning a user to a space with a role
class UserSpaceRoleAssignmentPayload(BaseModel):
    user_id: uuid.UUID = Field(..., description="ID of the user to assign to the space")
    role_name: str = Field(..., description="Name of the role to assign to the user within the space")

# Schema for displaying a user's role within a space
class UserSpaceRoleDisplay(BaseModel):
    user: UserDisplay
    role: RoleDisplay # Using the global RoleDisplay, assuming roles are global but contextually applied
    assigned_at: datetime = Field(alias="created_at") # Assuming 'created_at' from UserSpaceRole model

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


# Schema for displaying detailed space information including members and their roles
class SpaceDetailsDisplay(SpaceDisplay):
    members: List[UserSpaceRoleDisplay] = []

    class Config:
        orm_mode = True
