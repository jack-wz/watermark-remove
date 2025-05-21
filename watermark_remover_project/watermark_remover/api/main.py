import fastapi
from fastapi import FastAPI, File, UploadFile, HTTPException
from starlette.responses import FileResponse
import uvicorn
import os
import shutil
import uuid

# Adjust the import path based on the project structure
# Assuming main.py is in watermark_remover/api/ and lama_wrapper.py is in watermark_remover/core/
from watermark_remover.core.lama_wrapper import LaMaWrapper

# Initialize FastAPI app
app = FastAPI(title="Watermark Remover API", version="0.1.0")

# Instantiate LaMaWrapper
# For a PoC, a global instance is fine. For production, consider lifespan management.
lama_wrapper = LaMaWrapper() # Assuming default model path or placeholder doesn't need one

# Define temporary directories for API file handling
# These paths are relative to the project root (where this script might be run from)
# or need to be absolute. For simplicity, let's assume running from project root
# or adjust paths accordingly.
# For robustness, construct paths relative to this file's location.
API_TEMP_BASE_DIR = os.path.join(os.path.dirname(__file__), "../../../data/api_temp")
API_INPUT_DIR = os.path.join(API_TEMP_BASE_DIR, "input")
API_OUTPUT_DIR = os.path.join(API_TEMP_BASE_DIR, "output")

# Ensure these directories exist
os.makedirs(API_INPUT_DIR, exist_ok=True)
os.makedirs(API_OUTPUT_DIR, exist_ok=True)

@app.post("/v1/remove_watermark_single/", response_class=FileResponse)
async def remove_watermark_single_endpoint(file: UploadFile = File(...)):
    """
    Receives an image file, removes the watermark (placeholder: converts to grayscale),
    and returns the processed image.
    """
    temp_input_filename = f"temp_input_{uuid.uuid4()}_{file.filename}"
    temp_output_filename = f"temp_output_{uuid.uuid4()}_{file.filename}"
    
    input_file_path = os.path.join(API_INPUT_DIR, temp_input_filename)
    output_file_path = os.path.join(API_OUTPUT_DIR, temp_output_filename)

    try:
        # Save uploaded file
        with open(input_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Process with LaMaWrapper
        processed_image_path = lama_wrapper.remove_watermark(input_file_path, output_file_path)

        if not os.path.exists(processed_image_path):
            raise HTTPException(status_code=500, detail="Error processing image: Output file not found.")

        # Return processed image
        # The FileResponse will automatically handle streaming the file.
        # The media_type can be inferred from the filename or explicitly set.
        return FileResponse(processed_image_path, media_type=file.content_type, filename=file.filename)

    except FileNotFoundError as e:
        # Specific error from LaMaWrapper if input file to it was not found (should be caught by earlier checks too)
        raise HTTPException(status_code=404, detail=f"File not found during processing: {e}")
    except HTTPException as e:
        # Re-raise HTTPExceptions if they are already raised
        raise e
    except Exception as e:
        # Catch-all for other errors
        # Log the error for debugging: print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
    finally:
        # Cleanup: Delete temporary input and output files
        if os.path.exists(input_file_path):
            os.remove(input_file_path)
        # The output_file_path might be the same as processed_image_path
        if os.path.exists(output_file_path) and output_file_path != processed_image_path: # just in case wrapper changes output path
             os.remove(output_file_path)
        # If processed_image_path is different and exists, it should also be cleaned up if not returned directly by FileResponse
        # However, FileResponse handles the file, so usually we don't delete it here unless it's a copy
        # For this PoC, if processed_image_path IS output_file_path, it's handled by FileResponse.
        # If LaMaWrapper could return a *different* path than the one we provided for output,
        # then that temporary file also needs cleanup. Assuming it uses the provided output_file_path.

if __name__ == "__main__":
    # This allows running the app with `python main.py`
    # The string "main:app" refers to the file `main.py` and the variable `app`.
    # `reload=True` is useful for development.
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
```
