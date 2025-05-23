from sqlalchemy.orm import Session
from . import models, schemas # schemas will be created later
from .security import get_password_hash, verify_password

# User CRUD operations
def get_user_by_username(db: Session, username: str) -> models.User | None:
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_email(db: Session, email: str) -> models.User | None:
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate) -> models.User: # UserCreate schema to be defined
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name # Assuming UserCreate will have full_name
    )
    db.add(db_user)
    db.commit() # Commit to get user_id

    # Assign default role
    default_role_name = "viewer" # As seeded in 0002_seed_default_roles.py
    role = get_role_by_name(db, default_role_name)
    if role:
        db_user.roles.append(role)
        db.commit() # Commit the role assignment
    else:
        # Log a warning or handle if the default role is not found
        # This might happen if migrations haven't run or seeding failed
        print(f"Warning: Default role '{default_role_name}' not found. User '{db_user.username}' will not have a default role.")
        # Depending on policy, you might want to raise an error here instead.

    db.refresh(db_user) # Refresh to get the roles loaded in the user object if needed immediately
    return db_user

def authenticate_user(db: Session, username: str, password: str) -> models.User | None:
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not user.hashed_password: # Should not happen for local accounts
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

# Role and UserRole operations (placeholders, can be expanded)
def get_role_by_name(db: Session, role_name: str) -> models.Role | None:
    return db.query(models.Role).filter(models.Role.role_name == role_name).first()

def assign_role_to_user(db: Session, user: models.User, role: models.Role):
    user.roles.append(role)
    db.commit()
    db.refresh(user) # Refresh to load the new role association
    return user

# Admin User Management Service Functions
import uuid # Make sure uuid is imported

def get_user_by_id(db: Session, user_id: uuid.UUID) -> models.User | None:
    return db.query(models.User).filter(models.User.user_id == user_id).first()

def list_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
    return db.query(models.User).offset(skip).limit(limit).all()

def assign_role_to_user_by_id(db: Session, user_id: uuid.UUID, role_name: str) -> models.User | None:
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        return None # User not found
    
    role = get_role_by_name(db, role_name=role_name)
    if not role:
        return None # Role not found
        
    # Check if user already has the role
    current_role_names = {r.role_name for r in user.roles}
    if role_name in current_role_names:
        return user # Already has the role, return user as is or could raise an exception/return specific code

    user.roles.append(role)
    db.commit()
    db.refresh(user)
    return user

# Ingested Document Service Functions

def get_ingested_document_by_id(db: Session, doc_id: uuid.UUID) -> models.IngestedDocument | None:
    """
    Retrieves an ingested document by its ID.
    """
    # Consider eager loading related data if needed for display, e.g., uploader or space details
    # For now, just fetching the document itself.
    return db.query(models.IngestedDocument).filter(models.IngestedDocument.doc_id == doc_id).first()

def create_sso_user(
    db: Session, 
    email: str, 
    sso_provider: str, 
    sso_subject_id: str, 
    full_name: str | None = None,
    # username: str | None = None # Could add a specific username if provided by OIDC and desired
) -> models.User:
    """
    Creates a new user for SSO login.
    Password is not set for these users.
    Username can be derived from email or be a unique generated string if not provided.
    """
    # Use email as username for simplicity if no specific username is provided
    # Ensure this meets your system's unique constraints for usernames if SSO users share the same username space as local users.
    # A more robust approach might be to ensure User.username is nullable and not used as primary login for SSO users.
    derived_username = email # Or generate something like f"{sso_provider}_{sso_subject_id}" if email is not unique enough or not desired as username.

    db_user = models.User(
        email=email,
        username=derived_username, # Make sure this is unique or handle potential conflicts
        sso_provider=sso_provider,
        sso_subject_id=sso_subject_id,
        full_name=full_name,
        is_active=True, # SSO users are typically active by default
        hashed_password=None # No local password for SSO-only users
    )
    db.add(db_user)
    try:
        db.commit()
    except Exception as e: # Catch potential integrity errors (e.g. unique constraint on username if derived_username conflicts)
        db.rollback()
        # Check if it's a unique constraint violation for username
        existing_user_by_username = get_user_by_username(db, username=derived_username)
        if existing_user_by_username:
            # This means the derived username (e.g. email) is already taken by another user.
            # This can happen if a local account already used that email as their username.
            # Handle this case: e.g., append a random string, or require manual intervention.
            # For now, re-raise a more specific error or the original one.
            raise ValueError(f"Username '{derived_username}' derived from email already exists. Cannot create SSO user.") from e
        raise e # Re-raise other commit errors

    db.refresh(db_user)

    # Assign default role (e.g., 'viewer')
    default_role_name = "viewer"
    role = get_role_by_name(db, default_role_name)
    if role:
        db_user.roles.append(role)
        db.commit()
        db.refresh(db_user) # Refresh again to get roles loaded
    else:
        print(f"Warning: Default role '{default_role_name}' not found for SSO user '{email}'.")
        
    return db_user

# Space Management Service Functions
from sqlalchemy.orm import joinedload # For eager loading
from typing import List # Ensure List is imported

def create_space(db: Session, space_data: schemas.SpaceCreate, creator: models.User) -> models.Space:
    db_space = models.Space(
        space_name=space_data.space_name,
        space_type=space_data.space_type,
        description=space_data.description,
        created_by_user_id=creator.user_id
        # creator relationship will be set if back_populates is correct and session is managed
    )
    db.add(db_space)
    db.commit()
    db.refresh(db_space)
    return db_space

def list_spaces(db: Session, skip: int = 0, limit: int = 100) -> List[models.Space]:
    return db.query(models.Space).options(joinedload(models.Space.creator)).offset(skip).limit(limit).all()

def get_space_by_id(db: Session, space_id: uuid.UUID) -> models.Space | None:
    return db.query(models.Space).options(joinedload(models.Space.creator)).filter(models.Space.space_id == space_id).first()

def assign_user_to_space_with_role(
    db: Session, 
    space: models.Space, 
    user: models.User, 
    role: models.Role
) -> models.UserSpaceRole | None:
    """
    Assigns a user to a space with a specific role.
    Returns the UserSpaceRole association object.
    """
    # Check if the assignment already exists
    existing_assignment = db.query(models.UserSpaceRole).filter_by(
        user_id=user.user_id,
        space_id=space.space_id,
        # role_id=role.role_id # A user can have multiple roles in a space, so this check might be too restrictive
                               # Or, if a user can only have ONE role per space, this check is valid.
                               # For now, let's assume multiple roles are possible, so we only check user+space for an existing role.
                               # If a specific role needs to be checked for existence, filter by role_id too.
    ).first()

    # More precise check: does this user ALREADY have THIS specific role in this space?
    current_user_role_in_space = db.query(models.UserSpaceRole).filter_by(
        user_id=user.user_id,
        space_id=space.space_id,
        role_id=role.role_id 
    ).first()

    if current_user_role_in_space:
        return current_user_role_in_space # Or raise an error indicating already assigned

    db_user_space_role = models.UserSpaceRole(
        user_id=user.user_id,
        space_id=space.space_id,
        role_id=role.role_id
    )
    db.add(db_user_space_role)
    db.commit()
    db.refresh(db_user_space_role)
    return db_user_space_role

def list_users_in_space_with_roles(db: Session, space: models.Space) -> List[models.UserSpaceRole]:
    """
    Lists all users and their roles within a specific space.
    Returns a list of UserSpaceRole association objects.
    """
    # Eager load user and role details to avoid N+1 queries when accessing them later
    return db.query(models.UserSpaceRole)\
        .filter(models.UserSpaceRole.space_id == space.space_id)\
        .options(joinedload(models.UserSpaceRole.user), joinedload(models.UserSpaceRole.role))\
        .all()

def revoke_role_from_user_by_id(db: Session, user_id: uuid.UUID, role_name: str) -> models.User | None:
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        return None # User not found

    role_to_revoke = None
    for role in user.roles:
        if role.role_name == role_name:
            role_to_revoke = role
            break
    
    if not role_to_revoke:
        return None # User does not have this role, or role name doesn't exist (though get_role_by_name could check this too)

    user.roles.remove(role_to_revoke)
    db.commit()
    db.refresh(user)
    return user
