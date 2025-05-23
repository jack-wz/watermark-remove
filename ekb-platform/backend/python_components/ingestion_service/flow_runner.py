import yaml
import os
import uuid # For current_user_id, space_id types
from typing import Any, Dict, Optional, List as PyList # Renamed to PyList to avoid conflict with SQLAlchemy's List
from sqlalchemy.orm import Session
from sentence_transformers import SentenceTransformer 

from .. import models # To import models.IngestedDocument, models.DocumentChunk
from .text_utils import chunk_text # Import the chunking utility

# Initialize the Sentence Transformer model (e.g., all-MiniLM-L6-v2)
# This model will be loaded once when the module is imported.
# In a production FastAPI app, consider loading during startup events.
MODEL_NAME = 'all-MiniLM-L6-v2'
print(f"Loading sentence transformer model: {MODEL_NAME}...")
try:
    embedding_model = SentenceTransformer(MODEL_NAME)
    print(f"Model '{MODEL_NAME}' loaded successfully.")
except Exception as e:
    print(f"Error loading sentence transformer model '{MODEL_NAME}': {e}")
    embedding_model = None # Set to None if loading fails


# Conceptual path to where CocoIndex flow definitions are stored
# This might be configured via environment variables or a settings module in a real app.
FLOW_DEFINITIONS_BASE_PATH = os.path.join(
    os.path.dirname(__file__), # Current directory (ingestion_service)
    '..', # Up to python_components
    '..', # Up to backend
    '..', # Up to ekb-platform
    'cocoindex_flows',
    'flows_definitions'
)

# Placeholder for CocoIndex's actual Python client/library
# class CocoIndexClient:
#     def __init__(self, config_path=None):
#         # Load CocoIndex global config, connect to its services, etc.
#         print(f"CocoIndexClient initialized (conceptually). Config path: {config_path}")
#
#     def execute_flow(self, flow_definition: Dict, input_data: Dict) -> Dict:
#         # This would make calls to the CocoIndex engine
#         print(f"Executing flow: {flow_definition.get('flow_name')} with input: {input_data}")
#         # Simulate processing based on flow steps (conceptual)
#         output = {"status": "success", "message": "Flow executed conceptually."}
#         if 'steps' in flow_definition:
#             for step in flow_definition['steps']:
#                 print(f"  - Running step: {step.get('name')} using {step.get('processor')}")
#         output["processed_data"] = {"extracted_text": "Some text from input_data"} # Dummy output
#         return output

# coco_client = CocoIndexClient() # Initialize a client instance

def load_flow_definition(flow_name: str) -> Dict | None:
    """
    Loads a flow definition from a YAML (or JSON) file.
    The flow_name is expected to match the filename (without extension).
    """
    flow_file_path_yaml = os.path.join(FLOW_DEFINITIONS_BASE_PATH, f"{flow_name}.yaml")
    flow_file_path_json = os.path.join(FLOW_DEFINITIONS_BASE_PATH, f"{flow_name}.json")

    flow_file_path = None
    if os.path.exists(flow_file_path_yaml):
        flow_file_path = flow_file_path_yaml
    elif os.path.exists(flow_file_path_json):
        flow_file_path = flow_file_path_json
    else:
        print(f"Error: Flow definition file not found for flow '{flow_name}' in {FLOW_DEFINITIONS_BASE_PATH}")
        return None

    try:
        with open(flow_file_path, 'r') as f:
            if flow_file_path.endswith(".yaml") or flow_file_path.endswith(".yml"):
                flow_def = yaml.safe_load(f)
            elif flow_file_path.endswith(".json"):
                # import json # Add import json at the top
                # flow_def = json.load(f)
                pass # JSON loading not yet implemented for this placeholder
            else:
                print(f"Error: Unsupported file format for flow definition: {flow_file_path}")
                return None
        return flow_def
    except Exception as e:
        print(f"Error loading flow definition '{flow_name}': {e}")
        return None

def run_flow(
    flow_definition: Dict, 
    input_data: Dict, 
    db: Session, 
    current_user_id: uuid.UUID, 
    space_id: Optional[uuid.UUID] = None
) -> models.IngestedDocument:
    """
    Simulates running a CocoIndex flow, extracts text from a file,
    and stores an IngestedDocument record in the database.
    """
    flow_name = flow_definition.get("flow_name", "Unnamed Flow")
    print(f"Attempting to run flow: {flow_name} for user {current_user_id}")
    
    file_path = input_data.get("file_path")
    original_filename = input_data.get("original_filename", "unknown_file")

    if not file_path or not os.path.exists(file_path):
        # This should ideally be caught before calling run_flow
        raise ValueError(f"File not found at path: {file_path}")

    extracted_text_content = ""
    doc_type_from_flow = "unknown" # Default

    # Simulate steps from flow_definition (conceptual)
    if 'steps' in flow_definition:
        for step in flow_definition['steps']:
            processor = step.get('processor')
            if processor == "file_reader_processor":
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        # For this placeholder, we assume the input_data for this step
                        # would be the file_path, and its output is the content.
                        # In a real CocoIndex, data flows between steps.
                        file_content_for_next_step = f.read()
                        print(f"  Step '{step.get('name')}': Read file content.")
                except Exception as e:
                    print(f"  Error in step '{step.get('name')}': {e}")
                    # Handle error, maybe set status to 'failed' and raise
                    raise IOError(f"Could not read file content from {file_path}: {e}") from e
            
            elif processor == "markdown_text_extractor_processor":
                # Here, we'd use a real Markdown library if this were not conceptual.
                # For now, the "extracted_text" is just the raw content.
                # Assume `file_content_for_next_step` is available from previous step.
                extracted_text_content = file_content_for_next_step # Placeholder
                doc_type_from_flow = "markdown" # Set based on this processor
                print(f"  Step '{step.get('name')}': Conceptually extracted text (used raw content).")

    # Create IngestedDocument record
    # The source_uri is the path to the *temporarily saved* uploaded file.
    # In a more robust system, this file might be moved to permanent storage by CocoIndex,
    # and source_uri would be updated to that permanent location.
    db_ingested_document = models.IngestedDocument(
        source_uri=file_path, # Using temp file path as source_uri for now
        doc_type=doc_type_from_flow,
        extracted_text=extracted_text_content,
        doc_metadata={ # Basic metadata
            "original_filename": original_filename,
            "size_bytes": input_data.get("size_bytes"),
            "content_type": input_data.get("content_type"),
            "flow_name": flow_name,
        },
        space_id=space_id,
        uploaded_by_user_id=current_user_id,
        processing_status='completed' # Assuming direct processing for now
        # last_processed_at will be set by DB default or trigger if not here
    )
    
    db.add(db_ingested_document)
    db.commit() # Commit the parent document first to ensure it has an ID
    db.refresh(db_ingested_document)

    # 2. Chunk the extracted text
    if extracted_text_content and embedding_model:
        text_chunks = chunk_text(extracted_text_content) # Uses default chunking strategy from text_utils
        
        print(f"  Generated {len(text_chunks)} chunks for document {db_ingested_document.doc_id}.")

        for i, chunk_content in enumerate(text_chunks):
            # 3. Generate embedding for each chunk
            # Ensure the model is loaded and ready
            if embedding_model:
                chunk_embedding = embedding_model.encode(chunk_content)
            else:
                chunk_embedding = None # Or handle error: model not loaded
                print(f"  Warning: Embedding model not loaded. Skipping embedding for chunk {i}.")

            # 4. Create DocumentChunk record
            db_document_chunk = models.DocumentChunk(
                doc_id=db_ingested_document.doc_id,
                chunk_text=chunk_content,
                embedding=chunk_embedding,
                chunk_order=i
            )
            db.add(db_document_chunk)
        
        if text_chunks: # If chunks were created and added
            db.commit() # Commit all chunks for the document
            print(f"  Successfully stored {len(text_chunks)} chunks with embeddings.")
    
    print(f"Flow execution finished for: {flow_name}. Document ID: {db_ingested_document.doc_id}")
    return db_ingested_document


if __name__ == '__main__':
    # Example of how to use these functions (for testing this module directly)
    # This part would need a database session and user/space IDs to run now.
    # print(f"Looking for flows in: {FLOW_DEFINITIONS_BASE_PATH}")
    
    # # Test loading the markdown_parser_flow
    # flow_def = load_flow_definition("markdown_parser_flow")
    # if flow_def:
    #     print("\nSuccessfully loaded flow definition:")
    #     # print(yaml.dump(flow_def, indent=2)) # Pretty print YAML
        
    #     print("\nRunning the flow with conceptual input:")
    #     # Conceptual input for a markdown file processing flow
    #     # This mock input needs to be adjusted as file_path is now primary.
    #     # Create a dummy file for testing:
    #     dummy_file_path = os.path.join(FLOW_DEFINITIONS_BASE_PATH, "..", "temp_uploads", "test_flow_runner.md")
    #     os.makedirs(os.path.dirname(dummy_file_path), exist_ok=True)
    #     with open(dummy_file_path, "w") as f:
    #         f.write("# Test Markdown\nThis is a test.")

    #     mock_input_for_run = {
    #         "file_path": dummy_file_path,
    #         "original_filename": "test_flow_runner.md",
    #         "size_bytes": os.path.getsize(dummy_file_path),
    #         "content_type": "text/markdown"
    #     }
        
        # Need a mock DB session and IDs to run this test now.
        # from ..db.session import SessionLocal # Example
        # test_db = SessionLocal()
        # test_user_id = uuid.uuid4() 
        # try:
        #    result_doc = run_flow(flow_def, mock_input_for_run, db=test_db, current_user_id=test_user_id)
        #    print("\nFlow execution result (IngestedDocument object):")
        #    print(result_doc)
        #    # Clean up test document from DB if necessary, or use a test DB.
        #    test_db.delete(result_doc)
        #    test_db.commit()
        # finally:
        #    test_db.close()
        #    if os.path.exists(dummy_file_path):
        #        os.remove(dummy_file_path)

    else:
        print("Failed to load markdown_parser_flow definition.")
    # Example of how to use these functions (for testing this module directly)
    print(f"Looking for flows in: {FLOW_DEFINITIONS_BASE_PATH}")
    
    # Test loading the markdown_parser_flow
    flow_def = load_flow_definition("markdown_parser_flow")
    if flow_def:
        print("\nSuccessfully loaded flow definition:")
        # print(yaml.dump(flow_def, indent=2)) # Pretty print YAML
        
        print("\nRunning the flow with conceptual input:")
        # Conceptual input for a markdown file processing flow
        mock_input = {
            "source_uri": "path/to/uploaded/example.md",
            "file_content": "# Example Markdown\n\nThis is *some* text."
            # In a real scenario, input_data might just be a reference (e.g., file_id, s3_key)
            # and the first step of the flow would fetch the actual data.
        }
        result = run_flow(flow_def, mock_input)
        print("\nFlow execution result (conceptual):")
        # print(yaml.dump(result, indent=2))
    else:
        print("Failed to load markdown_parser_flow definition.")
