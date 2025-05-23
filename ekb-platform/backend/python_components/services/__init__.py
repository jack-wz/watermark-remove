# This file makes services a Python package.

# Import service functions to make them available through the package, e.g.:
# from services.user_service import create_user, get_user_by_username
# from services.auth_service import authenticate_user
# from services.admin_service import list_users

# For now, keeping it simple. Specific imports can be done from the modules.
# Alternatively, selectively expose functions:

from .services import (
    get_user_by_username,
    get_user_by_email,
    create_user,
    authenticate_user,
    get_role_by_name,
    assign_role_to_user,
    get_user_by_id,
    list_users,
    assign_role_to_user_by_id,
    create_sso_user,
    create_space,
    list_spaces,
    get_space_by_id,
    assign_user_to_space_with_role,
    list_users_in_space_with_roles,
    revoke_role_from_user_by_id,
    get_ingested_document_by_id
)

# Import from the new search_service.py
from .search_service import semantic_search

# Import from the new audit_service.py
from .audit_service import create_audit_log
