import uuid
from typing import List, Any, Optional # Import Optional
from datetime import datetime # Import datetime for date filtering

from fastapi import APIRouter, Depends, HTTPException, status, Path, Body, Query # Import Query
from sqlalchemy.orm import Session

from .. import schemas, services, models
from ..db.session import get_db
from ..security import require_role

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_role("admin"))] # Protect all routes in this router
)

@router.get("/users", response_model=List[schemas.UserDisplay])
async def read_users_list(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> Any:
    """
    Retrieve a list of users with pagination.
    Accessible only by users with the 'admin' role.
    """
    users = services.list_users(db, skip=skip, limit=limit)
    return users

@router.post("/users/{user_id}/roles", response_model=schemas.UserDisplay)
async def admin_assign_role_to_user(
    user_id: uuid.UUID = Path(..., description="The ID of the user to assign the role to"),
    role_op: schemas.UserRoleOperation = Body(...),
    db: Session = Depends(get_db)
) -> Any:
    """
    Assign a specific role to a user.
    Accessible only by users with the 'admin' role.
    """
    db_user = services.get_user_by_id(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    role_name = role_op.role_name
    db_role = services.get_role_by_name(db, role_name=role_name)
    if not db_role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Role '{role_name}' not found")

    # Check if user already has the role
    user_role_names = {role.role_name for role in db_user.roles}
    if role_name in user_role_names:
        # Or return 200 OK with current state if preferred
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"User already has role '{role_name}'")
        
    updated_user = services.assign_role_to_user_by_id(db, user_id=user_id, role_name=role_name)
    if not updated_user: 
        # This case should ideally be caught by previous checks, but as a safeguard:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to assign role")
    return updated_user


@router.delete("/users/{user_id}/roles/{role_name}", response_model=schemas.UserDisplay)
async def admin_revoke_role_from_user(
    user_id: uuid.UUID = Path(..., description="The ID of the user to revoke the role from"),
    role_name: str = Path(..., description="The name of the role to revoke"),
    db: Session = Depends(get_db)
) -> Any:
    """
    Revoke a specific role from a user.
    Accessible only by users with the 'admin' role.
    """
    db_user = services.get_user_by_id(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    db_role = services.get_role_by_name(db, role_name=role_name)
    if not db_role: # Role itself doesn't exist
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Role '{role_name}' not found")

    # Check if user actually has the role
    user_role_names = {role.role_name for role in db_user.roles}
    if role_name not in user_role_names:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"User does not have role '{role_name}'")

    updated_user = services.revoke_role_from_user_by_id(db, user_id=user_id, role_name=role_name)
    if not updated_user:
         # This case should ideally be caught by previous checks, but as a safeguard:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to revoke role")
    return updated_user


@router.get("/audit-logs", response_model=schemas.AuditLogResponse)
async def read_audit_logs(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    user_id: Optional[uuid.UUID] = Query(None, description="Filter by User ID"),
    action: Optional[str] = Query(None, description="Filter by action (case-insensitive partial match)"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date/time (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date/time (ISO format)"),
    db: Session = Depends(get_db)
    # current_admin: models.User = Depends(require_role("admin")) # This is already applied to the whole router
) -> schemas.AuditLogResponse:
    """
    Retrieve audit logs with pagination and filtering.
    Accessible only by users with the 'admin' role.
    """
    logs, total_count = services.get_audit_logs(
        db=db, 
        page=page, 
        size=size, 
        user_id=user_id, 
        action=action, 
        start_date=start_date, 
        end_date=end_date
    )
    
    return schemas.AuditLogResponse(
        items=logs, # Pydantic will convert list of ORM models to list of AuditLogDisplay
        total=total_count,
        page=page,
        size=size
        # pages = (total_count + size - 1) // size # Example if adding total_pages
    )
