import uuid
import os
import shutil
from typing import Optional, Any

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request # Import Request
from sqlalchemy.orm import Session

from .. import schemas 
from .. import services # Import the services module
from ..db.session import get_db
from ..security import get_current_active_user
from ..models.user import User as UserModel # For type hinting current_user
from ..ingestion_service import flow_runner # Import flow_runner
# from ..core.config import settings # Not explicitly used here currently

router = APIRouter(
    prefix="/ingestion",
    tags=["ingestion"]
)

TEMP_UPLOAD_DIR = os.path.join(
    os.path.dirname(__file__), 
    '..', 
    'temp_uploads' 
)
os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)


@router.post("/upload/file", response_model=schemas.IngestionResponse)
async def upload_document_file(
    request: Request, # Add Request object
    space_id: Optional[uuid.UUID] = Form(None), 
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
) -> schemas.IngestionResponse:
    """
    Upload a file (assumed Markdown for now) for ingestion.
    """
    ip_address = request.client.host if request.client else "unknown"
    original_filename = file.filename if file.filename else "unknown_file"

    if not file.filename:
        # No audit log here as it's a basic validation failure before significant processing
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No filename provided.")

    if not file.filename.lower().endswith((".md", ".markdown")):
        services.create_audit_log(
            db=db, action='DOCUMENT_INGEST_FAILURE', success=False,
            user_id=current_user.user_id, username=current_user.username, ip_address=ip_address,
            details={'filename': original_filename, 'reason': 'Invalid file type'}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Invalid file type. Only Markdown files (.md, .markdown) are currently supported."
        )

    unique_filename = f"{uuid.uuid4()}_{original_filename}"
    temp_file_path = os.path.join(TEMP_UPLOAD_DIR, unique_filename)
    
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        services.create_audit_log(
            db=db, action='DOCUMENT_INGEST_FAILURE', success=False,
            user_id=current_user.user_id, username=current_user.username, ip_address=ip_address,
            details={'filename': original_filename, 'reason': 'Could not save uploaded file', 'error': str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not save uploaded file: {e}",
        )
    finally:
        file.file.close()

    input_data_for_flow = {
        "file_path": temp_file_path,
        "original_filename": original_filename,
        "content_type": file.content_type,
        "size_bytes": os.path.getsize(temp_file_path),
    }

    flow_definition = flow_runner.load_flow_definition("markdown_parser_flow")
    if not flow_definition:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        services.create_audit_log(
            db=db, action='DOCUMENT_INGEST_FAILURE', success=False,
            user_id=current_user.user_id, username=current_user.username, ip_address=ip_address,
            details={'filename': original_filename, 'reason': 'Could not load ingestion flow definition'}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not load ingestion flow definition.",
        )

    try:
        ingested_document = flow_runner.run_flow(
            flow_definition=flow_definition, 
            input_data=input_data_for_flow,
            db=db, 
            current_user_id=current_user.user_id,
            space_id=space_id
        )
        
        services.create_audit_log(
            db=db, action='DOCUMENT_INGEST_SUCCESS', success=True,
            user_id=current_user.user_id, username=current_user.username, ip_address=ip_address,
            details={
                'doc_id': str(ingested_document.doc_id), 
                'filename': original_filename, 
                'source_uri': ingested_document.source_uri,
                'space_id': str(space_id) if space_id else None
            }
        )
        
        response_data = schemas.IngestionResponse(
            doc_id=ingested_document.doc_id,
            source_uri=ingested_document.source_uri,
            doc_type=ingested_document.doc_type,
            processing_status=ingested_document.processing_status,
            message="File processed successfully.",
            space_id=ingested_document.space_id,
            uploaded_by_user_id=ingested_document.uploaded_by_user_id,
            doc_metadata=ingested_document.doc_metadata,
            created_at=ingested_document.created_at 
        )
        return response_data

    except (ValueError, IOError) as e_flow: # Catch specific errors from flow_runner
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        services.create_audit_log(
            db=db, action='DOCUMENT_INGEST_FAILURE', success=False,
            user_id=current_user.user_id, username=current_user.username, ip_address=ip_address,
            details={'filename': original_filename, 'reason': 'Error during flow execution', 'error': str(e_flow)}
        )
        # Determine appropriate status code based on error type
        status_code = status.HTTP_400_BAD_REQUEST if isinstance(e_flow, ValueError) else status.HTTP_500_INTERNAL_SERVER_ERROR
        raise HTTPException(status_code=status_code, detail=str(e_flow))
    except Exception as e_unhandled:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        services.create_audit_log(
            db=db, action='DOCUMENT_INGEST_FAILURE', success=False,
            user_id=current_user.user_id, username=current_user.username, ip_address=ip_address,
            details={'filename': original_filename, 'reason': 'Unhandled exception during flow execution', 'error': str(e_unhandled)}
        )
        print(f"Unhandled exception during flow execution: {type(e_unhandled).__name__} - {e_unhandled}") 
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during file processing flow: {type(e_unhandled).__name__}",
        )


@router.get("/documents/{doc_id}", response_model=schemas.IngestedDocumentDisplay)
async def read_ingested_document(
    request: Request, # Add Request object
    doc_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user) 
) -> schemas.IngestedDocumentDisplay:
    """
    Retrieve an ingested document by its ID.
    """
    ip_address = request.client.host if request.client else "unknown"
    document = services.get_ingested_document_by_id(db, doc_id=doc_id)
    
    if not document:
        # No audit log for "not found" typically, unless it's a security concern (e.g. probing)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    
    services.create_audit_log(
        db=db, action='DOCUMENT_VIEW', success=True,
        user_id=current_user.user_id, username=current_user.username, ip_address=ip_address,
        details={'doc_id': str(doc_id), 'source_uri': document.source_uri}
    )
    return document
