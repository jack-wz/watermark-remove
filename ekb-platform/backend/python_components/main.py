from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware # Import SessionMiddleware

from .core.config import settings # Import settings if needed for app configuration
from .routers import auth, admin, spaces, oidc, ingestion, search # Import all routers, including search
# from .db.session import engine # If you need to create tables directly (not recommended with Alembic)
# from .models import user # Import models if creating tables directly

# Base.metadata.create_all(bind=engine) # Not recommended if using Alembic

app = FastAPI(
    title=settings.PROJECT_NAME,
    # other FastAPI app settings
)

# Add SessionMiddleware for OIDC state handling
# Ensure settings.SECRET_KEY is a strong, randomly generated string for session security
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)


# Include routers
app.include_router(auth.router, prefix=settings.API_V1_STR) 
app.include_router(admin.router, prefix=settings.API_V1_STR) 
app.include_router(spaces.router, prefix=settings.API_V1_STR)
app.include_router(oidc.router, prefix=settings.API_V1_STR) 
app.include_router(ingestion.router, prefix=settings.API_V1_STR)
app.include_router(search.router, prefix=settings.API_V1_STR) # Include Search router

@app.get("/")
async def root():
    return {"message": f"Hello from {settings.PROJECT_NAME}"}

# Placeholder for agent runtime or other components
# from .agent_runtime import router as agent_router
# app.include_router(agent_router, prefix="/agent")

if __name__ == "__main__":
    import uvicorn
    # Ensure Uvicorn runs on host and port from settings or defaults
    uvicorn.run(app, host="0.0.0.0", port=8000) # Or use settings.SERVER_HOST, settings.SERVER_PORT if defined
