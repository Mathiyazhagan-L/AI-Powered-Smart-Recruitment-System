import os
import shutil
from uuid import uuid4
from fastapi import APIRouter, File, UploadFile, HTTPException, status
from fastapi.requests import Request

router = APIRouter(prefix="/uploads", tags=["Uploads"])

UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "uploads", "images"))
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/image")
async def upload_image(request: Request, file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be an image")
    
    ext = os.path.splitext(file.filename)[1]
    safe_filename = f"{uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to save image: {e}")
        
    # Construct the full URL
    base_url = str(request.base_url).rstrip("/")
    image_url = f"{base_url}/static_uploads/images/{safe_filename}"
    
    return {"url": image_url}
