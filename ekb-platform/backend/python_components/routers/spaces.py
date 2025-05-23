import uuid
from typing import List, Any

from fastapi import APIRouter, Depends, HTTPException, status, Path, Body
from sqlalchemy.orm import Session

from .. import schemas, services, models
from ..db.session import get_db
from ..security import get_current_active_user, require_role

router = APIRouter(
    prefix="/spaces",
    tags=["spaces"]
)

@router.post("", response_model=schemas.SpaceDisplay, status_code=status.HTTP_201_CREATED)
async def create_new_space(
    space_data: schemas.SpaceCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user) # Any authenticated user can create a space
) -> Any:
    """
    Create a new space.
    The creator will be the currently authenticated user.
    """
    new_space = services.create_space(db=db, space_data=space_data, creator=current_user)
    # Assign the creator as 'space_admin' for this new space
    admin_role = services.get_role_by_name(db, role_name="admin") # Assuming a global 'admin' role can act as space_admin
    if not admin_role:
        # Fallback or specific 'space_admin' role logic
        # This might indicate that the default roles weren't seeded correctly or a different role name should be used.
        # For now, we'll raise an error if the 'admin' role (intended for space administration) isn't found.
        # Consider seeding a specific 'space_admin' role if global 'admin' is not appropriate.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Default 'admin' role for space administration not found. Cannot assign space owner."
        )
    
    services.assign_user_to_space_with_role(db=db, space=new_space, user=current_user, role=admin_role)
    
    # Refresh space to include creator details in response if not automatically handled by ORM/schema
    # The SpaceDisplay schema expects a 'creator' field.
    # get_space_by_id includes options(joinedload(models.Space.creator))
    # Let's ensure the created space object has this loaded for the response.
    db.refresh(new_space) # Refresh to ensure all fields are up-to-date from DB
    if not new_space.creator: # If creator is not loaded by default after refresh
        new_space.creator = current_user # Manually set for response model

    return new_space

@router.get("", response_model=List[schemas.SpaceDisplay])
async def read_spaces_list(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user) # Any authenticated user can list spaces
) -> Any:
    """
    Retrieve a list of spaces with pagination.
    Accessible by any authenticated user.
    """
    spaces = services.list_spaces(db, skip=skip, limit=limit)
    return spaces

@router.get("/{space_id}", response_model=schemas.SpaceDetailsDisplay) # Use SpaceDetailsDisplay
async def read_space_details(
    space_id: uuid.UUID = Path(..., description="The ID of the space to retrieve"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user) # Or space member check
) -> Any:
    """
    Get details of a specific space, including its members and their roles.
    Accessible by any authenticated user (future: check membership).
    """
    db_space = services.get_space_by_id(db, space_id=space_id)
    if not db_space:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Space not found")
    
    # Get members and their roles for this space
    members_associations = services.list_users_in_space_with_roles(db, space=db_space)
    
    # Prepare the members list for the SpaceDetailsDisplay schema
    members_display_list = []
    for assoc in members_associations:
        members_display_list.append(
            schemas.UserSpaceRoleDisplay(
                user=schemas.UserDisplay.from_orm(assoc.user), # Map User model to UserDisplay
                role=schemas.RoleDisplay.from_orm(assoc.role),   # Map Role model to RoleDisplay
                assigned_at=assoc.created_at
            )
        )
    
    # Construct the response object
    space_details = schemas.SpaceDetailsDisplay(
        **schemas.SpaceDisplay.from_orm(db_space).dict(), # Populate base space fields
        members=members_display_list
    )
    return space_details


@router.post("/{space_id}/users", response_model=schemas.UserSpaceRoleDisplay)
async def assign_user_to_space(
    space_id: uuid.UUID = Path(..., description="The ID of the space"),
    assignment_payload: schemas.UserSpaceRoleAssignmentPayload = Body(...),
    db: Session = Depends(get_db),
    # Protected by global admin for now, future: space admin for the specific space_id
    admin_user: models.User = Depends(require_role("admin")) 
) -> Any:
    """
    Assign a user to a space with a specific role.
    Accessible only by users with the global 'admin' role.
    """
    db_space = services.get_space_by_id(db, space_id=space_id)
    if not db_space:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Space not found")

    target_user = services.get_user_by_id(db, user_id=assignment_payload.user_id)
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user not found")

    role_to_assign = services.get_role_by_name(db, role_name=assignment_payload.role_name)
    if not role_to_assign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Role '{assignment_payload.role_name}' not found")

    # Check if role is appropriate for spaces (e.g. 'admin', 'editor', 'viewer')
    # For now, any existing role can be assigned.
    # Future: Add a 'role_type' or filter applicable roles.

    assignment = services.assign_user_to_space_with_role(db, space=db_space, user=target_user, role=role_to_assign)
    if not assignment:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to assign user to space, user may already have this role in the space.")

    # Construct the response
    return schemas.UserSpaceRoleDisplay(
        user=schemas.UserDisplay.from_orm(target_user),
        role=schemas.RoleDisplay.from_orm(role_to_assign),
        assigned_at=assignment.created_at
    )

@router.get("/{space_id}/users", response_model=List[schemas.UserSpaceRoleDisplay])
async def list_users_in_space(
    space_id: uuid.UUID = Path(..., description="The ID of the space"),
    db: Session = Depends(get_db),
    # Protected by global admin or space member (future enhancement)
    current_user: models.User = Depends(get_current_active_user) 
) -> Any:
    """
    List all users and their roles within a specific space.
    Accessible by any authenticated user (future: check membership or space admin role).
    """
    db_space = services.get_space_by_id(db, space_id=space_id)
    if not db_space:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Space not found")

    members_associations = services.list_users_in_space_with_roles(db, space=db_space)
    
    response_list = []
    for assoc in members_associations:
        response_list.append(
             schemas.UserSpaceRoleDisplay(
                user=schemas.UserDisplay.from_orm(assoc.user),
                role=schemas.RoleDisplay.from_orm(assoc.role),
                assigned_at=assoc.created_at
            )
        )
    return response_list
