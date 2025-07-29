"""File management service for handling uploads, storage, and retrieval."""

import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from enum import Enum

import aiofiles
from fastapi import UploadFile, HTTPException
from PIL import Image
import io

from ..core.config import get_settings


class FileType(str, Enum):
    """File type categories."""
    IMAGE = "image"
    DOCUMENT = "document"


class FileManager:
    """File management service for handling file operations."""
    
    def __init__(self):
        """Initialize file manager with settings."""
        self.settings = get_settings()
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        directories = [
            self.settings.upload_dir,
            self.settings.images_dir,
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            print(f"確保目錄存在: {directory}")
    
    def _get_file_path(self, file_type: FileType, filename: str) -> str:
        """Get the appropriate file path based on file type."""
        base_paths = {
            FileType.IMAGE: self.settings.images_dir,
            FileType.DOCUMENT: self.settings.images_dir,  # Use images_dir for documents too
        }
        
        base_path = base_paths.get(file_type, self.settings.upload_dir)
        return os.path.join(base_path, filename)
    
    def _generate_unique_filename(
        self,
        original_filename: str,
        prefix: Optional[str] = None,
        include_timestamp: bool = True
    ) -> str:
        """Generate a unique filename."""
        file_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") if include_timestamp else ""
        
        # Get file extension
        file_extension = Path(original_filename).suffix
        
        # Build filename parts
        parts = []
        if prefix:
            parts.append(prefix)
        if timestamp:
            parts.append(timestamp)
        parts.append(file_id[:8])  # Short UUID
        
        filename_without_ext = "_".join(parts)
        return f"{filename_without_ext}{file_extension}"
    
    def validate_image_file(self, file: UploadFile) -> bool:
        """Validate uploaded image file."""
        # Check file extension
        if not file.filename:
            return False
        
        file_extension = Path(file.filename).suffix.lower()
        allowed_extensions = self.settings.get_allowed_image_types_list()
        
        if file_extension not in allowed_extensions:
            return False
        
        # Check content type
        if not file.content_type or not file.content_type.startswith('image/'):
            return False
        
        return True
    
    def validate_file_size(self, file_size: int, file_type: FileType) -> bool:
        """Validate file size based on type."""
        if file_type == FileType.IMAGE:
            return file_size <= self.settings.max_image_size
        else:
            return file_size <= self.settings.max_file_size
    
    async def save_image(
        self,
        file: UploadFile,
        prefix: Optional[str] = None,
        validate_image: bool = True
    ) -> Dict[str, Any]:
        """Save uploaded image file."""
        if not self.validate_image_file(file):
            raise HTTPException(
                status_code=400,
                detail="不支援的圖片格式。僅支援 JPG, PNG, GIF 格式"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Validate file size
        if not self.validate_file_size(len(file_content), FileType.IMAGE):
            raise HTTPException(
                status_code=400,
                detail=f"圖片檔案過大。最大允許大小為 {self.settings.max_image_size // 1024 // 1024}MB"
            )
        
        # Validate image content if required
        if validate_image:
            try:
                image = Image.open(io.BytesIO(file_content))
                image.verify()
            except Exception:
                raise HTTPException(status_code=400, detail="無效的圖片檔案")
        
        # Generate unique filename
        unique_filename = self._generate_unique_filename(
            file.filename,
            prefix=prefix
        )
        
        # Save file
        file_path = self._get_file_path(FileType.IMAGE, unique_filename)
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_content)
        
        return {
            "file_id": unique_filename,
            "original_filename": file.filename,
            "file_path": file_path,
            "file_size": len(file_content),
            "content_type": file.content_type,
            "file_type": FileType.IMAGE,
            "created_at": datetime.now().isoformat()
        }
    
    async def save_document(
        self,
        file_content: bytes,
        filename: str,
        content_type: str,
        prefix: Optional[str] = None
    ) -> Dict[str, Any]:
        """Save document file."""
        # Generate unique filename
        unique_filename = self._generate_unique_filename(
            filename,
            prefix=prefix
        )
        
        # Save file
        file_path = self._get_file_path(FileType.DOCUMENT, unique_filename)
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_content)
        
        return {
            "file_id": unique_filename,
            "original_filename": filename,
            "file_path": file_path,
            "file_size": len(file_content),
            "content_type": content_type,
            "file_type": FileType.DOCUMENT,
            "created_at": datetime.now().isoformat()
        }
    

    
    async def get_file(self, file_id: str, file_type: FileType) -> Optional[bytes]:
        """Retrieve file content by file ID."""
        file_path = self._get_file_path(file_type, file_id)
        
        if not os.path.exists(file_path):
            return None
        
        async with aiofiles.open(file_path, 'rb') as f:
            return await f.read()
    
    def get_file_info(self, file_id: str, file_type: FileType) -> Optional[Dict[str, Any]]:
        """Get file information."""
        file_path = self._get_file_path(file_type, file_id)
        
        if not os.path.exists(file_path):
            return None
        
        stat = os.stat(file_path)
        return {
            "file_id": file_id,
            "file_path": file_path,
            "file_size": stat.st_size,
            "file_type": file_type,
            "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
        }
    
    def list_files(self, file_type: FileType) -> List[Dict[str, Any]]:
        """List all files of a specific type."""
        base_path = self._get_file_path(file_type, "")
        
        if not os.path.exists(base_path):
            return []
        
        files = []
        for filename in os.listdir(base_path):
            file_path = os.path.join(base_path, filename)
            if os.path.isfile(file_path):
                stat = os.stat(file_path)
                files.append({
                    "file_id": filename,
                    "file_path": file_path,
                    "file_size": stat.st_size,
                    "file_type": file_type,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        
        return sorted(files, key=lambda x: x["created_at"], reverse=True)
    
    async def delete_file(self, file_id: str, file_type: FileType) -> bool:
        """Delete a file."""
        file_path = self._get_file_path(file_type, file_id)
        
        if not os.path.exists(file_path):
            return False
        
        try:
            os.remove(file_path)
            return True
        except Exception:
            return False
    



# Global file manager instance
file_manager = FileManager() 