import os
import re
import uuid
import aiofiles
from abc import ABC, abstractmethod
from typing import Tuple
from backend.app.core.config import settings

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent directory traversal and remove dangerous characters."""
    clean_name = os.path.basename(filename)
    clean_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', clean_name)
    if not clean_name or clean_name.startswith('.'):
        clean_name = f"document_{uuid.uuid4().hex[:8]}.pdf"
    return clean_name

class FileStorage(ABC):
    @abstractmethod
    async def save_file(self, content: bytes, user_id: str, document_id: str, filename: str) -> Tuple[str, int]:
        pass

    @abstractmethod
    def get_file_path(self, relative_path: str) -> str:
        pass

    @abstractmethod
    async def delete_file(self, relative_path: str) -> bool:
        pass

class LocalStorage(FileStorage):
    def __init__(self, base_dir: str = settings.STORAGE_DIR):
        self.base_dir = os.path.abspath(base_dir)
        os.makedirs(self.base_dir, exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, "uploads"), exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, "pages"), exist_ok=True)

    async def save_file(self, content: bytes, user_id: str, document_id: str, filename: str) -> Tuple[str, int]:
        safe_name = sanitize_filename(filename)
        _, ext = os.path.splitext(safe_name)
        user_dir = os.path.join(self.base_dir, "uploads", str(user_id))
        os.makedirs(user_dir, exist_ok=True)
        
        stored_filename = f"{document_id}{ext}"
        target_path = os.path.join(user_dir, stored_filename)

        # Ensure no path traversal outside base_dir
        if not os.path.abspath(target_path).startswith(self.base_dir):
            raise ValueError("Invalid target path: directory traversal attempt detected.")

        with open(target_path, "wb") as f:
            f.write(content)

        relative_path = os.path.relpath(target_path, self.base_dir).replace("\\", "/")
        return relative_path, len(content)

    def save_page_image_sync(self, image_bytes: bytes, document_id: str, page_num: int) -> str:
        page_dir = os.path.join(self.base_dir, "pages", str(document_id))
        os.makedirs(page_dir, exist_ok=True)
        page_filename = f"page_{page_num}.png"
        target_path = os.path.join(page_dir, page_filename)
        with open(target_path, "wb") as f:
            f.write(image_bytes)
        return os.path.relpath(target_path, self.base_dir).replace("\\", "/")

    def get_file_path(self, relative_path: str) -> str:
        safe_path = os.path.abspath(os.path.join(self.base_dir, relative_path))
        if not safe_path.startswith(self.base_dir):
            raise ValueError("Access outside storage boundary is forbidden.")
        return safe_path

    async def delete_file(self, relative_path: str) -> bool:
        try:
            full_path = self.get_file_path(relative_path)
            if os.path.exists(full_path):
                os.remove(full_path)
                return True
        except Exception:
            pass
        return False

storage = LocalStorage()
