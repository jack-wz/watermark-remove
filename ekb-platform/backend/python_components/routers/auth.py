from fastapi import APIRouter, Depends, HTTPException, status, Request # Import Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Any

from .. import schemas, services, models # services will now include create_audit_log
from ..db.session import get_db
# Import specific security functions and dependencies needed
from ..security import (
    create_access_token, 
    get_current_active_user, 
    require_role, # For the new admin endpoint
    # decode_access_token is used internally by get_current_user in security.py
    # oauth2_scheme is also now in security.py and used by get_current_user
)
from ..core.config import settings
from datetime import timedelta

router = APIRouter()

@router.post("/auth/signup", response_model=schemas.UserDisplay, status_code=status.HTTP_201_CREATED)
async def signup_new_user(
    user_payload: schemas.UserCreate, # Renamed to avoid clash with 'user' model instance
    request: Request, # Add Request object
    db: Session = Depends(get_db)
) -> Any:
    """
    Create new user.
    """
    ip_address = request.client.host if request.client else "unknown"
    try:
        db_user_by_username = services.get_user_by_username(db, username=user_payload.username)
        if db_user_by_username:
            services.create_audit_log(
                db=db, action='USER_SIGNUP_FAILURE', success=False,
                username=user_payload.username, ip_address=ip_address,
                details={'reason': 'Username already registered', 'email': user_payload.email}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered",
            )
        
        db_user_by_email = services.get_user_by_email(db, email=user_payload.email)
        if db_user_by_email:
            services.create_audit_log(
                db=db, action='USER_SIGNUP_FAILURE', success=False,
                username=user_payload.username, ip_address=ip_address,
                details={'reason': 'Email already registered', 'email': user_payload.email}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        
        new_user_obj = services.create_user(db=db, user=user_payload) # Renamed user to new_user_obj
        
        services.create_audit_log(
            db=db, action='USER_SIGNUP_SUCCESS', success=True,
            user_id=new_user_obj.user_id, username=new_user_obj.username, 
            ip_address=ip_address, details={'email': new_user_obj.email}
        )
        return new_user_obj
    except HTTPException: # Re-raise HTTPExceptions to let FastAPI handle them
        raise
    except Exception as e:
        # Log generic exception during signup
        services.create_audit_log(
            db=db, action='USER_SIGNUP_FAILURE', success=False,
            username=user_payload.username, ip_address=ip_address,
            details={'error': str(e), 'email': user_payload.email}
        )
        # It's important to not expose raw error messages to the client
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred during user registration.")


@router.post("/auth/login/token", response_model=schemas.Token)
async def login_for_access_token(
    request: Request, # Add Request object
    db: Session = Depends(get_db), 
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    ip_address = request.client.host if request.client else "unknown"
    authenticated_user = services.authenticate_user( # Renamed user to authenticated_user
        db, username=form_data.username, password=form_data.password
    )
    
    if not authenticated_user:
        services.create_audit_log(
            db=db, action='USER_LOGIN_FAILURE', success=False,
            username=form_data.username, ip_address=ip_address,
            details={'reason': 'Invalid credentials'}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not authenticated_user.is_active:
        services.create_audit_log(
            db=db, action='USER_LOGIN_FAILURE', success=False,
            user_id=authenticated_user.user_id, username=authenticated_user.username, 
            ip_address=ip_address, details={'reason': 'Inactive user'}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    
    services.create_audit_log(
        db=db, action='USER_LOGIN_SUCCESS', success=True,
        user_id=authenticated_user.user_id, username=authenticated_user.username, ip_address=ip_address
    )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": authenticated_user.username, "user_id": str(authenticated_user.user_id)}, 
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# get_current_user and get_current_active_user are now imported from security.py

@router.get("/users/me", response_model=schemas.UserDisplay)
async def read_users_me(
    current_user: models.User = Depends(get_current_active_user) # This now uses the imported dependency
) -> Any:
    """
    Fetch the current logged in user, including their roles.
    """
    # The get_current_active_user dependency (now in security.py) handles fetching the user.
    # The UserDisplay schema should be updated to include roles.
    # Accessing current_user.roles here (if not already loaded by get_current_active_user)
    # would trigger lazy loading if the UserDisplay schema needs it explicitly.
    # However, get_current_active_user in security.py was updated to touch roles.
    return current_user

# New admin-only test endpoint
@router.get("/admin/test", response_model=schemas.UserDisplay) # Or some other response
async def test_admin_endpoint(
    current_admin: models.User = Depends(require_role("admin"))
) -> Any:
    """
    Test endpoint accessible only by users with the 'admin' role.
    Returns the admin user's details.
    """
    return current_admin
