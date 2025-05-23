from fastapi import APIRouter, Depends, HTTPException, status
from starlette.requests import Request
from starlette.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
import secrets # For generating state

from .. import schemas, services, models
from ..db.session import get_db
from ..oidc_client import oauth # The initialized OAuth client
from ..core.config import settings
from ..security import create_access_token # For our application's JWT
from datetime import timedelta

router = APIRouter(
    prefix="/auth/oidc",
    tags=["oidc"]
)

# Ensure OIDC client is available
if not hasattr(oauth, 'oidc'):
    print("Error: OIDC client 'oidc' not found in oauth object. Check OIDC configuration and registration in oidc_client.py.")
    # Optionally raise an error or disable OIDC routes if not configured
    # For now, routes might fail if oauth.oidc is None

@router.get("/login")
async def oidc_login(request: Request): # No audit log here, as it's just a redirect initiation
    """
    Initiates the OIDC login flow by redirecting the user to the OIDC provider.
    """
    if not hasattr(oauth, 'oidc'):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="OIDC not configured")

    # Construct the redirect URI for the callback endpoint
    # Ensure this matches what's configured in your OIDC provider and in settings.OIDC_REDIRECT_URI
    # request.url_for('oidc_callback') might be more robust if using named routes and Starlette routing
    redirect_uri = settings.OIDC_REDIRECT_URI 
    if not redirect_uri.startswith("http"): # if it's a relative path from config
        redirect_uri = str(request.url_for('oidc_callback_full')) # Assuming 'oidc_callback_full' is the name of the callback route

    # Generate and store state for CSRF protection
    state = secrets.token_urlsafe(32)
    request.session['oidc_state'] = state # Requires Starlette SessionMiddleware

    return await oauth.oidc.authorize_redirect(request, redirect_uri, state=state)

@router.get("/callback", name="oidc_callback_full") # Give it a name for url_for
async def oidc_callback(request: Request, db: Session = Depends(get_db)):
    """
    Handles the callback from the OIDC provider after successful authentication.
    Exchanges the authorization code for tokens, validates them, and provisions/logs in the user.
    """
    if not hasattr(oauth, 'oidc'):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="OIDC not configured")

    ip_address = request.client.host if request.client else "unknown"
    sso_provider_name = 'oidc' # Or a more specific name

    # CSRF Protection: Check state
    expected_state = request.session.pop('oidc_state', None)
    received_state = request.query_params.get('state')

    if not expected_state or expected_state != received_state:
        services.create_audit_log(
            db=db, action='USER_OIDC_LOGIN_FAILURE', success=False,
            ip_address=ip_address, details={'reason': 'Invalid state parameter (CSRF protection)'}
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid state parameter for CSRF protection.")

    try:
        token = await oauth.oidc.authorize_access_token(request)
    except Exception as e:
        print(f"Error exchanging OIDC token: {e}")
        services.create_audit_log(
            db=db, action='USER_OIDC_LOGIN_FAILURE', success=False,
            ip_address=ip_address, details={'reason': 'Error exchanging authorization code for token', 'error': str(e)}
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error exchanging authorization code for token.")

    user_info_from_token = token.get('userinfo')
    if not user_info_from_token:
        try:
            id_token_claims = await oauth.oidc.parse_id_token(token)
            if not id_token_claims:
                services.create_audit_log(
                    db=db, action='USER_OIDC_LOGIN_FAILURE', success=False,
                    ip_address=ip_address, details={'reason': 'Could not retrieve user info from OIDC id_token claims.'}
                )
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not retrieve user info from OIDC provider (id_token).")
            user_info_from_token = id_token_claims
        except Exception as e:
            print(f"Error parsing OIDC id_token: {e}")
            services.create_audit_log(
                db=db, action='USER_OIDC_LOGIN_FAILURE', success=False,
                ip_address=ip_address, details={'reason': 'Error parsing id_token from OIDC provider', 'error': str(e)}
            )
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error parsing user info from OIDC provider.")


    sso_subject_id = user_info_from_token.get('sub')
    email = user_info_from_token.get('email')
    full_name = user_info_from_token.get('name') or user_info_from_token.get('preferred_username')

    if not sso_subject_id or not email:
        services.create_audit_log(
            db=db, action='USER_OIDC_LOGIN_FAILURE', success=False,
            ip_address=ip_address, 
            details={'reason': 'Missing required user information (subject_id or email) from OIDC provider.', 'sso_subject_id': sso_subject_id, 'email': email}
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing required user information (subject_id or email) from OIDC provider.")

    # User Provisioning/Linking
    user_model_instance = db.query(models.User).filter_by(sso_provider=sso_provider_name, sso_subject_id=sso_subject_id).first()

    is_new_user = False
    if not user_model_instance:
        existing_user_by_email = services.get_user_by_email(db, email=email)
        if existing_user_by_email:
            services.create_audit_log(
                db=db, action='USER_OIDC_LOGIN_FAILURE', success=False,
                username=email, ip_address=ip_address,
                details={'reason': 'Account with this email already exists, SSO not linked.', 'sso_subject_id': sso_subject_id}
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, 
                detail=f"An account with email '{email}' already exists. Please login with your existing credentials or contact support to link accounts."
            )
        else:
            try:
                user_model_instance = services.create_sso_user(db, email=email, sso_provider=sso_provider_name, sso_subject_id=sso_subject_id, full_name=full_name)
                is_new_user = True
            except ValueError as ve: # Catch username conflict from create_sso_user
                 services.create_audit_log(
                    db=db, action='USER_OIDC_PROVISIONING_FAILURE', success=False,
                    username=email, ip_address=ip_address,
                    details={'reason': str(ve), 'sso_subject_id': sso_subject_id}
                )
                 raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(ve))
            except Exception as e:
                services.create_audit_log(
                    db=db, action='USER_OIDC_PROVISIONING_FAILURE', success=False,
                    username=email, ip_address=ip_address,
                    details={'error': str(e), 'sso_subject_id': sso_subject_id}
                )
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to provision user: {str(e)}")

    if not user_model_instance.is_active:
        services.create_audit_log(
            db=db, action='USER_OIDC_LOGIN_FAILURE', success=False,
            user_id=user_model_instance.user_id, username=user_model_instance.username, 
            ip_address=ip_address, details={'reason': 'Inactive user'}
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User account is inactive.")

    action_type = 'USER_OIDC_PROVISIONING_SUCCESS' if is_new_user else 'USER_OIDC_LOGIN_SUCCESS'
    services.create_audit_log(
        db=db, action=action_type, success=True,
        user_id=user_model_instance.user_id, username=user_model_instance.username, 
        ip_address=ip_address, details={'sso_subject_id': sso_subject_id}
    )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    app_access_token = create_access_token(
        data={"sub": user_model_instance.username or user_model_instance.email, "user_id": str(user_model_instance.user_id)},
        expires_delta=access_token_expires
    )

    # Redirect to frontend with token (preferred for web clients)
    # This assumes frontend is on a different port or host and has /oidc-callback route
    # frontend_callback_url = f"http://localhost:3000/oidc-callback?token={app_access_token}" 
    # For now, returning JSON as per original structure; frontend needs to handle this.
    # If redirecting, use: return RedirectResponse(url=frontend_callback_url)
    
    return JSONResponse({
        "access_token": app_access_token, 
        "token_type": "bearer",
        "user_info": schemas.UserDisplay.from_orm(user_model_instance).dict()
    })

# Note: SessionMiddleware needs to be added to FastAPI's main app for request.session to work.
# Example: from starlette.middleware.sessions import SessionMiddleware
# app.add_middleware(SessionMiddleware, secret_key="your-session-secret-key")
# This secret key should be strong and from config.
