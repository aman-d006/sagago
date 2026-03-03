import os
import uuid
import io
from fastapi import UploadFile, HTTPException
from core.config import settings

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("Warning: PIL not available, images will be saved without optimization")

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
MAX_FILE_SIZE = settings.MAX_UPLOAD_SIZE

# Get absolute base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

async def save_upload_file(upload_file: UploadFile, subdir: str = "stories") -> str:
    # Check file extension
    file_ext = os.path.splitext(upload_file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type {file_ext} not allowed. Allowed: {ALLOWED_EXTENSIONS}")
    
    # Read file contents
    contents = await upload_file.read()
    file_size = len(contents)
    
    # Check file size
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File too large. Max size: {MAX_FILE_SIZE/1024/1024}MB")
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    filename = f"{file_id}{file_ext}"
    
    # Create absolute directory path
    upload_dir = os.path.join(BASE_DIR, settings.UPLOAD_DIR, subdir)
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, filename)
    
    print(f"💾 Saving file to: {file_path}")
    
    if HAS_PIL:
        # Optimize image with PIL
        try:
            img = Image.open(io.BytesIO(contents))
            
            # Convert RGBA to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            
            # Resize if too large (max 1200x1200)
            img.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
            
            # Save with optimization
            img.save(file_path, optimize=True, quality=85)
            print(f"✅ Image saved with optimization: {file_path}")
            
        except Exception as e:
            print(f"❌ PIL processing failed: {e}, falling back to direct save")
            with open(file_path, "wb") as f:
                f.write(contents)
    else:
        # Save directly without optimization
        with open(file_path, "wb") as f:
            f.write(contents)
        print(f"✅ Image saved directly: {file_path}")
    
    # Return the URL path
    return f"/uploads/{subdir}/{filename}"

def delete_upload_file(file_url: str):
    """Delete uploaded file by URL"""
    if not file_url or not file_url.startswith("/uploads/"):
        return
    
    file_path = file_url.replace("/uploads/", "")
    full_path = os.path.join(BASE_DIR, settings.UPLOAD_DIR, file_path)
    
    if os.path.exists(full_path):
        os.remove(full_path)
        print(f"🗑️ Deleted file: {full_path}")