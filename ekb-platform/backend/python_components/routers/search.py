from fastapi import APIRouter, Depends, HTTPException, status, Request # Import Request
from sqlalchemy.orm import Session
from typing import Any 

from .. import schemas, services 
from ..db.session import get_db
from ..security import get_current_active_user
from ..models.user import User as UserModel # For type hinting current_user

router = APIRouter(
    prefix="/search",
    tags=["search"]
)

@router.post("/semantic", response_model=schemas.SearchResponse)
async def perform_semantic_search(
    request_obj: Request, # Renamed 'request' to 'request_obj' to avoid conflict if 'request' is used as a variable
    search_payload: schemas.SearchQueryRequest, # Renamed to avoid conflict
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user) 
) -> schemas.SearchResponse:
    """
    Perform semantic search on document chunks based on a query text.
    Requires authentication.
    """
    ip_address = request_obj.client.host if request_obj.client else "unknown"
    num_results = 0 # Default in case of error before results are fetched
    
    try:
        search_results_items = services.semantic_search(
            db=db, 
            query_text=search_payload.query_text, 
            top_k=search_payload.top_k
        )
        num_results = len(search_results_items)
        
        services.create_audit_log(
            db=db, action='SEARCH_PERFORMED', success=True,
            user_id=current_user.user_id, username=current_user.username, ip_address=ip_address,
            details={'query': search_payload.query_text, 'top_k': search_payload.top_k, 'num_results': num_results}
        )
        
        return schemas.SearchResponse(
            query_text=search_payload.query_text,
            results=search_results_items
        )
    except RuntimeError as e_runtime: # Catch specific errors like model not loaded
        services.create_audit_log(
            db=db, action='SEARCH_FAILURE', success=False,
            user_id=current_user.user_id, username=current_user.username, ip_address=ip_address,
            details={'query': search_payload.query_text, 'top_k': search_payload.top_k, 'error': str(e_runtime), 'reason': 'Model not loaded'}
        )
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e_runtime))
    except Exception as e_generic:
        services.create_audit_log(
            db=db, action='SEARCH_FAILURE', success=False,
            user_id=current_user.user_id, username=current_user.username, ip_address=ip_address,
            details={'query': search_payload.query_text, 'top_k': search_payload.top_k, 'error': str(e_generic)}
        )
        print(f"Unexpected error during semantic search: {type(e_generic).__name__} - {e_generic}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during search.")
