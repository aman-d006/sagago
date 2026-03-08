import os
import uuid
import shutil
from pathlib import Path
from fastapi import UploadFile, HTTPException
from datetime import datetime
import logging

from core.config import settings
from db.database import get_turso_client, settings as db_settings

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'}
MAX_FILE_SIZE = 10 * 1024 * 1024 

async def save_upload_file(file: UploadFile, subfolder: str = "stories", user_id: int = None, story_id: int = None) -> str:
    """Save uploaded file and return URL"""
    try:
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"File type {file_ext} not allowed")

        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"File size too large. Max {MAX_FILE_SIZE//(1024*1024)}MB")
        
        unique_id = str(uuid.uuid4())
        filename = f"{unique_id}{file_ext}"
        
      
        upload_dir = Path(settings.UPLOAD_DIR) / subfolder
        upload_dir.mkdir(parents=True, exist_ok=True)
        
      
        file_path = upload_dir / filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
       
        url_path = f"/uploads/{subfolder}/{filename}"

        if db_settings.USE_TURSO:
            try:
                with get_turso_client() as client:
                    user_id_str = str(user_id) if user_id else "NULL"
                    story_id_str = str(story_id) if story_id else "NULL"
                    
                    client.execute(
                        f"""
                        INSERT INTO images (
                            filename, original_filename, file_path, url_path, 
                            file_size, mime_type, user_id, story_id, created_at
                        ) VALUES (
                            '{filename}', '{file.filename.replace("'", "''")}', 
                            '{str(file_path)}', '{url_path}', 
                            {file_size}, '{file.content_type}', 
                            {user_id_str}, {story_id_str}, CURRENT_TIMESTAMP
                        )
                        """,
                        []
                    )
                    logger.info(f"✅ Image metadata saved to database: {filename}")
            except Exception as e:
                logger.error(f"Error saving image metadata: {e}")
        
        logger.info(f"✅ File saved: {filename}")
        return url_path
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

async def delete_upload_file(file_url: str) -> bool:
    """Delete uploaded file by URL"""
    try:
    
        filename = os.path.basename(file_url)
        
        
        if db_settings.USE_TURSO:
            with get_turso_client() as client:
                result = client.query_one(
                    f"SELECT file_path FROM images WHERE url_path = '{file_url}' OR filename = '{filename}'",
                    []
                )
                if result:
                    file_path = result[0]['value'] if isinstance(result[0], dict) else result[0]
                 
                    client.execute(
                        f"DELETE FROM images WHERE url_path = '{file_url}' OR filename = '{filename}'",
                        []
                    )
                else:
                   
                    for subfolder in ['stories', 'avatars']:
                        potential_path = Path(settings.UPLOAD_DIR) / subfolder / filename
                        if potential_path.exists():
                            file_path = str(potential_path)
                            break
                    else:
                        logger.warning(f"File not found in database: {filename}")
                        return False
        else:
            # Try to find in filesystem
            file_path = None
            for subfolder in ['stories', 'avatars']:
                potential_path = Path(settings.UPLOAD_DIR) / subfolder / filename
                if potential_path.exists():
                    file_path = str(potential_path)
                    break
        
        # Delete physical file
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"✅ File deleted: {file_path}")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        return False

def get_image_url(filename: str, subfolder: str = "stories") -> str:
    """Get URL for an image by filename"""
    return f"/uploads/{subfolder}/{filename}"

def get_image_metadata(image_id: int = None, filename: str = None) -> dict:
    """Get image metadata from database"""
    if not db_settings.USE_TURSO:
        return None
    
    try:
        with get_turso_client() as client:
            if image_id:
                result = client.query_one(
                    f"SELECT * FROM images WHERE id = {image_id}",
                    []
                )
            elif filename:
                result = client.query_one(
                    f"SELECT * FROM images WHERE filename = '{filename}'",
                    []
                )
            else:
                return None
            
            if result:
                return {
                    "id": result[0]['value'] if isinstance(result[0], dict) else result[0],
                    "filename": result[1]['value'] if isinstance(result[1], dict) else result[1],
                    "original_filename": result[2]['value'] if isinstance(result[2], dict) else result[2],
                    "file_path": result[3]['value'] if isinstance(result[3], dict) else result[3],
                    "url_path": result[4]['value'] if isinstance(result[4], dict) else result[4],
                    "file_size": result[5]['value'] if isinstance(result[5], dict) else result[5],
                    "mime_type": result[6]['value'] if isinstance(result[6], dict) else result[6],
                    "user_id": result[7]['value'] if isinstance(result[7], dict) else result[7],
                    "story_id": result[8]['value'] if isinstance(result[8], dict) else result[8],
                    "created_at": result[9]['value'] if isinstance(result[9], dict) else result[9]
                }
            return None
    except Exception as e:
        logger.error(f"Error getting image metadata: {e}")
        return None