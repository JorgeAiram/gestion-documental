import hashlib
import os
import shutil
from pathlib import Path
from typing import Tuple
from backend.config import STORAGE_DIR

def store_binary_file(file_bytes: bytes) -> Tuple[str, int, str]:
    """
    Stores a binary file using its SHA-256 hash as the filename.
    Provides automatic deduplication: if identical file content was uploaded,
    it reuses the existing stored binary, saving disk space.
    Returns: (sha256_hash, file_size_in_bytes, storage_file_path)
    """
    sha256_hash = hashlib.sha256(file_bytes).hexdigest()
    target_path = STORAGE_DIR / sha256_hash

    # Save only if not already stored (deduplication)
    if not target_path.exists():
        with open(target_path, "wb") as f:
            f.write(file_bytes)

    return sha256_hash, len(file_bytes), str(target_path)

def read_binary_file(storage_path: str) -> bytes:
    with open(storage_path, "rb") as f:
        return f.read()

def verify_file_integrity(storage_path: str, expected_hash: str) -> bool:
    if not os.path.exists(storage_path):
        return False
    with open(storage_path, "rb") as f:
        data = f.read()
    return hashlib.sha256(data).hexdigest() == expected_hash

def extract_text_content(filename: str, file_bytes: bytes) -> str:
    """Extract plain text for search and diff purposes if text or markdown."""
    ext = filename.lower().split('.')[-1] if '.' in filename else ''
    if ext in ['txt', 'md', 'csv', 'json', 'xml', 'html', 'js', 'css', 'py', 'sql', 'log', 'ini', 'cfg']:
        try:
            return file_bytes.decode('utf-8', errors='ignore')[:100000] # up to 100KB indexed
        except Exception:
            return ""
    return ""
