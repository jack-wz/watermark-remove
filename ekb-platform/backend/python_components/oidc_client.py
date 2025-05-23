from authlib.integrations.starlette_client import OAuth
from .core.config import settings

oauth = OAuth()

# Ensure OIDC settings are provided before attempting to register the client
if settings.OIDC_CLIENT_ID and settings.OIDC_CLIENT_SECRET and settings.OIDC_DISCOVERY_URL:
    oauth.register(
        name='oidc', # Default name, can be anything
        client_id=settings.OIDC_CLIENT_ID,
        client_secret=settings.OIDC_CLIENT_SECRET,
        server_metadata_url=settings.OIDC_DISCOVERY_URL,
        client_kwargs={
            'scope': 'openid email profile', # Standard OIDC scopes
            # 'token_endpoint_auth_method': 'client_secret_basic', # Or other method if required by provider
            # 'response_type': 'code', # Standard for OIDC auth code flow
        }
    )
else:
    print("Warning: OIDC client not registered due to missing configuration (CLIENT_ID, CLIENT_SECRET, or DISCOVERY_URL).")

# You might need to expose the 'oidc' client specifically if you have multiple providers
# oidc_provider = oauth.create_client('oidc') # This would fail if not registered.
# For now, the router will access it via oauth.oidc (if registered)
