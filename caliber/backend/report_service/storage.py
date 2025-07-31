"""
File storage utilities for report service
"""
import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional, BinaryIO
import logging

logger = logging.getLogger(__name__)

class FileStorage:
    """Handles file storage operations"""
    
    def __init__(self, base_path: str = "storage"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
    
    def save_file(self, file_content: bytes, filename: str, subdirectory: str = "") -> str:
        """Save a file to storage"""
        subdir_path = self.base_path / subdirectory
        subdir_path.mkdir(exist_ok=True)
        
        file_path = subdir_path / filename
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        logger.info(f"File saved: {file_path}")
        return str(file_path)
    
    def get_file_path(self, filename: str, subdirectory: str = "") -> Optional[str]:
        """Get the full path to a stored file"""
        file_path = self.base_path / subdirectory / filename
        if file_path.exists():
            return str(file_path)
        return None
    
    def delete_file(self, filename: str, subdirectory: str = "") -> bool:
        """Delete a stored file"""
        file_path = self.base_path / subdirectory / filename
        if file_path.exists():
            file_path.unlink()
            logger.info(f"File deleted: {file_path}")
            return True
        return False
    
    def list_files(self, subdirectory: str = "") -> list:
        """List all files in a subdirectory"""
        subdir_path = self.base_path / subdirectory
        if not subdir_path.exists():
            return []
        
        return [f.name for f in subdir_path.iterdir() if f.is_file()]
    
    def read_file(self, file_path: str) -> bytes:
        """Read file content as bytes"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(path, 'rb') as f:
            return f.read()
    
    def create_temp_file(self, suffix: str = "", prefix: str = "caliber_") -> str:
        """Create a temporary file and return its path"""
        temp_file = tempfile.NamedTemporaryFile(
            mode='w+b',
            suffix=suffix,
            prefix=prefix,
            delete=False,
            dir=self.base_path
        )
        temp_file.close()
        return temp_file.name
    
    def cleanup_temp_files(self, max_age_hours: int = 24):
        """Clean up temporary files older than specified age"""
        import time
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        for file_path in self.base_path.rglob("*"):
            if file_path.is_file() and file_path.name.startswith("caliber_"):
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_seconds:
                    try:
                        file_path.unlink()
                        logger.info(f"Cleaned up old temp file: {file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to delete temp file {file_path}: {e}")

# Global file storage instance
file_storage = FileStorage() 